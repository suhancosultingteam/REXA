from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import json
import re
import threading
import time
from rexa import run
from rexa.infra.logger import setup_logger
from rexa.tools._utils import KUMHA_BUILDING_CODE

import requests
from flask import Flask, jsonify, request

KAKAO_VERSION = "2.0"

logger = setup_logger(__name__)


def _json_log(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    except TypeError:
        return str(payload)


def _emit_log(label: str, payload: Any) -> None:
    message = f"{label}={_json_log(payload) if isinstance(payload, (dict, list)) else payload}"
    logger.info(message)
    print(message, flush=True)


class KakaoCallbackError(Exception):
    pass


@dataclass
class CallbackResult:
    task_id: Optional[str]
    status: str
    message: Optional[str]
    timestamp: Optional[int]
    raw: Dict[str, Any]


class KakaoChatbotResponse:
    @staticmethod
    def template(
            outputs: List[Dict[str, Any]],
            quick_replies: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "version": KAKAO_VERSION,
            "template": {
                "outputs": outputs,
            },
        }
        if quick_replies:
            payload["template"]["quickReplies"] = quick_replies
        return payload

    @staticmethod
    def callback_ack(
            data: Optional[Dict[str, Any]] = None,
            context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        스킬 서버가 즉시 반환할 응답.
        콜백 모드에서는 template 없이 useCallback=true 반환.
        """
        payload: Dict[str, Any] = {
            "version": KAKAO_VERSION,
            "useCallback": True,
        }
        if context is not None:
            payload["context"] = context
        if data is not None:
            payload["data"] = data
        return payload

    @staticmethod
    def simple_text(
            text: str,
            quick_replies: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return KakaoChatbotResponse.template(
            outputs=[{"simpleText": {"text": text}}],
            quick_replies=quick_replies,
        )

    @staticmethod
    def simple_image(image_url: str, alt_text: str) -> Dict[str, Any]:
        return {
            "simpleImage": {
                "imageUrl": image_url,
                "altText": alt_text,
            }
        }

    @staticmethod
    def text_card(
            title: str,
            description: str,
            buttons: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        card: Dict[str, Any] = {
            "title": title,
            "description": description,
        }
        if buttons:
            card["buttons"] = buttons
        return {"textCard": card}

    @staticmethod
    def basic_card(
            title: str,
            description: str,
            thumbnail_url: Optional[str] = None,
            buttons: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        card: Dict[str, Any] = {
            "title": title,
            "description": description,
        }
        if thumbnail_url:
            card["thumbnail"] = {"imageUrl": thumbnail_url}
        if buttons:
            card["buttons"] = buttons

        return {"basicCard": card}

    @staticmethod
    def commerce_card(
            title: str,
            description: str,
            price: int,
            currency: str = "won",
            thumbnail_url: Optional[str] = None,
            buttons: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        card: Dict[str, Any] = {
            "title": title,
            "description": description,
            "price": price,
            "currency": currency,
        }
        if thumbnail_url:
            card["thumbnails"] = [{"imageUrl": thumbnail_url}]
        if buttons:
            card["buttons"] = buttons
        return {"commerceCard": card}

    @staticmethod
    def item_card(
            image_title: str,
            image_description: str,
            image_url: str,
            item_list: List[Dict[str, Any]],
            item_list_summary: Optional[Dict[str, Any]] = None,
            thumbnail_width: Optional[int] = None,
            thumbnail_height: Optional[int] = None,
            profile_text: Optional[str] = None,
            profile_image_url: Optional[str] = None,
            buttons: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        card: Dict[str, Any] = {
            "imageTitle": {
                "title": image_title,
                "description": image_description,
            },
            "thumbnail": {
                "imageUrl": image_url,
            },
            "itemList": item_list,
        }
        if thumbnail_width is not None:
            card["thumbnail"]["width"] = thumbnail_width
        if thumbnail_height is not None:
            card["thumbnail"]["height"] = thumbnail_height
        if item_list_summary:
            card["itemListSummary"] = item_list_summary
        if profile_text:
            profile: Dict[str, Any] = {"nickname": profile_text}
            if profile_image_url:
                profile["imageUrl"] = profile_image_url
            card["profile"] = profile
        if buttons:
            card["buttons"] = buttons
        return {"itemCard": card}

    @staticmethod
    def list_card(
            header_title: str,
            items: List[Dict[str, Any]],
            buttons: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        card: Dict[str, Any] = {
            "header": {"title": header_title},
            "items": items,
        }
        if buttons:
            card["buttons"] = buttons

        return {"listCard": card}

    @staticmethod
    def carousel(
            carousel_type: str,
            items: List[Dict[str, Any]],
            header: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": carousel_type,
            "items": items,
        }
        if header:
            payload["header"] = header
        return {"carousel": payload}

    @staticmethod
    def quick_reply(
            label: str,
            message_text: str,
            action: str = "message",
    ) -> Dict[str, Any]:
        return {
            "label": label,
            "action": action,
            "messageText": message_text,
        }

    @staticmethod
    def web_link_button(label: str, url: str) -> Dict[str, Any]:
        return {
            "action": "webLink",
            "label": label,
            "webLinkUrl": url,
        }

    @staticmethod
    def phone_button(label: str, phone_number: str) -> Dict[str, Any]:
        return {
            "action": "phone",
            "label": label,
            "phoneNumber": phone_number,
        }

    @staticmethod
    def message_button(label: str, message_text: str) -> Dict[str, Any]:
        return {
            "action": "message",
            "label": label,
            "messageText": message_text,
        }

    @staticmethod
    def block_button(label: str, block_id: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "action": "block",
            "label": label,
            "blockId": block_id,
        }
        if extra:
            payload["extra"] = extra
        return payload

    @staticmethod
    def web_link(url: str) -> Dict[str, Any]:
        return {"web": url}


class KakaoCallbackClient:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    @staticmethod
    def extract_callback_url(skill_payload: Dict[str, Any]) -> str:
        try:
            return skill_payload["userRequest"]["callbackUrl"]
        except KeyError as e:
            raise KakaoCallbackError(
                "payload 안에 userRequest.callbackUrl 이 없습니다."
            ) from e

    def send_callback(
            self,
            callback_url: str,
            response_payload: Dict[str, Any],
    ) -> CallbackResult:
        _emit_log("callback request url", callback_url)
        _emit_log("callback request body", response_payload)
        try:
            resp = requests.post(
                callback_url,
                json=response_payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
        except requests.RequestException as e:
            raise KakaoCallbackError(f"콜백 HTTP 요청 실패: {e}") from e

        _emit_log("callback http status", resp.status_code)
        _emit_log("callback response text", resp.text)

        try:
            body = resp.json()
        except Exception as e:
            _emit_log("callback response non_json", {"status": resp.status_code, "body": resp.text})
            raise KakaoCallbackError(
                f"콜백 응답이 JSON이 아닙니다. status={resp.status_code}, body={resp.text}"
            ) from e

        _emit_log("callback response body", body)

        result = CallbackResult(
            task_id=body.get("taskId"),
            status=body.get("status", "UNKNOWN"),
            message=body.get("message"),
            timestamp=body.get("timestamp"),
            raw=body,
        )

        if resp.status_code >= 400:
            raise KakaoCallbackError(
                f"콜백 HTTP 오류: {resp.status_code}, "
                f"status={result.status}, message={result.message}"
            )

        if result.status not in ("SUCCESS", "FAIL", "ERROR"):
            raise KakaoCallbackError(f"알 수 없는 콜백 상태: {result.raw}")

        if result.status != "SUCCESS":
            raise KakaoCallbackError(
                f"콜백 실패: status={result.status}, "
                f"message={result.message}, raw={result.raw}"
            )

        return result


app = Flask(__name__)
callback_client = KakaoCallbackClient(timeout=10)

FEEDBACK_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfuIMUBJR_KbMZl-crc58eEel0tIkMkkYwP-Ky5_cH2Jf574g/viewform"
FEEDBACK_FORM_USER_ID_ENTRY = "entry.1213398873"


def _feedback_url(user_id: Optional[str]) -> str:
    url = FEEDBACK_FORM_URL
    if user_id:
        url = f"{url}?{urlencode({FEEDBACK_FORM_USER_ID_ENTRY: user_id})}"
    return url


def _build_feedback_button(user_id: Optional[str]) -> Dict[str, Any]:
    return KakaoChatbotResponse.web_link_button("피드백 보내기", _feedback_url(user_id))


def _build_feedback_card(user_id: Optional[str]) -> Dict[str, Any]:
    return KakaoChatbotResponse.text_card(
        title="피드백을 남겨주세요",
        description="더 나은 서비스를 위해 의견을 들려주세요.",
        buttons=[_build_feedback_button(user_id)],
    )


def extract_user_id(skill_payload: Dict[str, Any]) -> Optional[str]:
    user = skill_payload.get("userRequest", {}).get("user", {})
    return user.get("id") or user.get("properties", {}).get("botUserKey")


def extract_chat_debug_info(skill_payload: Dict[str, Any]) -> Dict[str, Any]:
    user_request = skill_payload.get("userRequest", {})
    return {
        "chatId": user_request.get("chatId"),
        "user": user_request.get("user"),
        "block": user_request.get("block"),
        "params": user_request.get("params"),
        "contexts": skill_payload.get("contexts"),
        "action": skill_payload.get("action"),
        "intent": skill_payload.get("intent"),
    }


def _mask_area_number(text: str) -> str:
    match = re.match(r"^(\d+)(\.\d+)?(.*)$", text)
    if not match:
        return text
    integer_part, decimal_part, suffix = match.groups()
    masked_integer = "*" if len(integer_part) <= 1 else integer_part[:-1] + "*"
    return f"{masked_integer}{decimal_part or ''}{suffix}"


def _format_area(value: Any, mask: bool = False) -> str:
    if value in (None, ""):
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    pyeong = number / 3.305785
    if mask:
        sqm_str = _mask_area_number(f"{int(number)}㎡")
        pyeong_str = _mask_area_number(f"{int(round(pyeong))}평")
    else:
        sqm_str = f"{int(number)}㎡" if number.is_integer() else f"{number:.1f}㎡"
        pyeong_str = f"{int(round(pyeong))}평"
    return f"{sqm_str} ({pyeong_str})"


_format_suhan_area = _format_area
_format_rent_area = _format_area


def _flatten_suhan_listings(retrieval_payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(retrieval_payload, dict):
        return []

    results = retrieval_payload.get("get_suhan_property")
    if not isinstance(results, list):
        return []

    listings: List[Dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict) or result.get("error"):
            continue
        result_listings = result.get("listings")
        if not isinstance(result_listings, list):
            continue
        for listing in result_listings:
            if isinstance(listing, dict):
                listings.append(listing)
    return listings


def _flatten_suhan_rent_listings(retrieval_payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(retrieval_payload, dict):
        return []

    results = retrieval_payload.get("get_suhan_rent_property")
    if not isinstance(results, list):
        return []

    listings: List[Dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict) or result.get("error"):
            continue
        result_listings = result.get("listings")
        if not isinstance(result_listings, list):
            continue
        for listing in result_listings:
            if isinstance(listing, dict):
                listings.append(listing)
    return listings


def _build_suhan_rent_property_carousel(listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []

    for listing in listings[:10]:
        address = listing.get("address") or {}
        rent_unit = listing.get("rent_unit") or {}
        deposit = rent_unit.get("deposit") or {}
        monthly_rent = rent_unit.get("monthly_rent") or {}
        maintenance_fee = rent_unit.get("maintenance_fee") or {}
        move_in_date_text = rent_unit.get("move_in_date_text" or "-")
        should_mask_area = listing.get("code") != KUMHA_BUILDING_CODE

        image_url = str(listing.get("base_url") or "https://placehold.co/800x400/png")
        name = str(listing.get("name") or address.get("jibun") or "-")
        floor_label = str(rent_unit.get("floor_label") or "-")
        jibun_addr = str(address.get("jibun") or "-")
        road_addr = str(address.get("road") or "-")
        rental_area = _format_rent_area(rent_unit.get("rental_area_sqm"), mask=should_mask_area)
        exclusive_area = _format_rent_area(rent_unit.get("exclusive_area_sqm"), mask=should_mask_area)
        deposit_text = str(deposit.get("human") or deposit.get("krw") or "-")
        monthly_rent_text = str(monthly_rent.get("human") or monthly_rent.get("krw") or "-")
        maintenance_fee_text = str(maintenance_fee.get("human") or maintenance_fee.get("krw") or "-")

        item: Dict[str, Any] = {
            "imageTitle": {
                "title": jibun_addr,
                "description": road_addr,
            },
            "thumbnail": {
                "imageUrl": image_url,
                "width": 800,
                "height": 400,
            },
            "itemList": [
                {"title" : "층 정보", "description" : floor_label},
                {"title": "임대면적", "description": rental_area},
                {"title": "전용면적", "description": exclusive_area},
                {"title" : "입주시기", "description": move_in_date_text},
                {"title": "보증금", "description": deposit_text},
                {
                    "title": "관리비",
                    "description": maintenance_fee_text,
                },
            ],
            "itemListAlignment": "right",
            "itemListSummary": {"title": "월 임대료", "description": monthly_rent_text},

        }
        items.append(item)

    return KakaoChatbotResponse.carousel("itemCard", items)


def _build_suhan_property_carousel(listings: List[Dict[str, Any]]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []

    for listing in listings[:10]:
        address = listing.get("address") or {}
        price = listing.get("price") or {}
        area = listing.get("area") or {}
        image_url = str(listing.get("base_url") or "https://placehold.co/800x400/png")
        jibun_addr = str(address.get("jibun") or "-")
        road_addr = str(address.get("road") or "-")
        code = str(listing.get("code") or "-")
        should_mask_area = listing.get("code") != KUMHA_BUILDING_CODE
        land_area = _format_suhan_area(area.get("land_sqm"), mask=should_mask_area)
        total_area = _format_suhan_area(area.get("total_sqm"), mask=should_mask_area)
        price_text = str(price.get("human") or price.get("krw") or "-")

        items.append(
            {
                "imageTitle": {
                    "title": jibun_addr,
                    "description": road_addr,
                },
                "thumbnail": {
                    "imageUrl": image_url,
                    "width": 800,
                    "height": 400,
                },
                "itemList": [
                    {"title": "매물코드", "description": code},
                    {"title": "대지면적", "description": land_area},
                    {"title": "연면적", "description": total_area},
                ],
                "itemListAlignment": "right",
                "itemListSummary": {
                    "title": "가격",
                    "description": price_text,
                },
            }
        )

    return KakaoChatbotResponse.carousel("itemCard", items)


KUMHA_BUILDING_URL = "https://suhan.co.kr/kumhabuilding"


def _build_openchat_inquiry_card(
        user_id: Optional[str],
        extra_buttons: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    buttons: List[Dict[str, Any]] = list(extra_buttons or [])
    buttons.append(
        KakaoChatbotResponse.web_link_button(
            "1:1 오픈카톡",
            "https://open.kakao.com/o/ssIaX8wi",
        )
    )
    buttons.append(_build_feedback_button(user_id))
    return KakaoChatbotResponse.text_card(
        title="추가 상담 안내",
        description="상업용 자산 검토는 1:1 상담으로 더 자세히 도와드릴 수 있습니다.",
        buttons=buttons,
    )


def build_final_response(
        user_text: str,
        user_id: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if metadata is None:
        raw_response = run(user_text, user_id=user_id)
    else:
        raw_response = run(user_text, user_id=user_id, metadata=metadata)
    try:
        response_payload = json.loads(raw_response)
    except json.JSONDecodeError:
        logger.warning("rexa.run returned non-JSON response, falling back to raw text")
        response_payload = {
            "query": user_text,
            "answer": raw_response,
        }

    answer = str(response_payload.get("answer") or "").strip()
    query_type = str(response_payload.get("query_type") or "").strip().upper()
    retrieval = response_payload.get("retrieval")
    suhan_listings = _flatten_suhan_listings(retrieval)
    suhan_rent_listings = _flatten_suhan_rent_listings(retrieval)
    if not answer:
        answer = "답변을 생성하지 못했어요. 잠시 후 다시 시도해주세요."

    has_building_price = bool(retrieval) and "get_building_price" in retrieval and any(
        isinstance(r, dict) and "error" not in r
        for r in retrieval.get("get_building_price", [])
    )

    if suhan_listings:
        outputs = [
            {"simpleText": {"text": answer}},
            _build_suhan_property_carousel(suhan_listings),
            _build_openchat_inquiry_card(user_id),
        ]
    elif suhan_rent_listings:
        outputs = [
            {"simpleText": {"text": answer}},
            _build_suhan_rent_property_carousel(suhan_rent_listings),
            _build_openchat_inquiry_card(
                user_id,
                extra_buttons=[
                    KakaoChatbotResponse.web_link_button("금하빌딩 페이지", KUMHA_BUILDING_URL),
                ],
            ),
        ]
    elif query_type == "C":
        outputs = [
            {"simpleText": {"text": answer}},
            _build_openchat_inquiry_card(user_id),
        ]
    elif has_building_price:
        outputs = [
            {"simpleText": {"text": answer}},
            _build_openchat_inquiry_card(user_id),
        ]
    else:
        outputs = [{"simpleText": {"text": answer}}, _build_feedback_card(user_id)]

    return KakaoChatbotResponse.template(outputs=outputs)


def process_and_callback(skill_payload: Dict[str, Any], request_id: Optional[str] = None) -> None:
    """
    별도 스레드에서 실제 처리 후 callbackUrl 로 최종 응답 전송.
    """
    try:
        _emit_log("callback worker start request_id", request_id)
        callback_url = KakaoCallbackClient.extract_callback_url(skill_payload)
        utterance = skill_payload.get("userRequest", {}).get("utterance", "")
        user_id = extract_user_id(skill_payload)

        _emit_log("callback_url", callback_url)
        _emit_log("utterance", utterance)
        _emit_log("user_id", user_id)

        # 예시: 오래 걸리는 작업 흉내
        time.sleep(2)

        final_payload = build_final_response(
            utterance,
            user_id,
            metadata={
                "channel": "kakao",
                "kakao_request_id": request_id,
                "chat_debug": extract_chat_debug_info(skill_payload),
            },
        )
        _emit_log("callback final_payload", final_payload)
        result = callback_client.send_callback(callback_url, final_payload)

        logger.info(
            "callback success task_id=%s status=%s message=%s raw=%s",
            result.task_id,
            result.status,
            result.message,
            result.raw,
        )

    except Exception as e:
        logger.exception("callback worker failed: %s", e)


@app.route("/kakao/skill", methods=["POST"])
def kakao_skill():
    skill_payload = request.get_json(force=True, silent=False)
    session_id = request.headers.get("X-Request-Id")
    user_id = extract_user_id(skill_payload)
    chat_debug_info = extract_chat_debug_info(skill_payload)

    print(f"Kakao raw_payload={json.dumps(skill_payload, ensure_ascii=False)}", flush=True)
    print(f"Kakao session_id={session_id}", flush=True)
    print(f"Kakao user_id={user_id}", flush=True)
    print(f"Kakao chat_debug={chat_debug_info}", flush=True)
    logger.info("kakao_skill start session_id=%s user_id=%s", session_id, user_id)
    logger.info("incoming payload=%s", skill_payload)

    # 1) 콜백 작업은 별도 스레드에서 실행
    worker = threading.Thread(
        target=process_and_callback,
        args=(skill_payload, session_id),
        daemon=True,
    )
    worker.start()
    logger.info("callback worker spawned name=%s alive=%s", worker.name, worker.is_alive())

    # 2) 즉시 useCallback=true 반환
    # 필요하면 data/context 추가 가능
    ack_payload = KakaoChatbotResponse.callback_ack()
    logger.info("ack payload=%s", _json_log(ack_payload))
    return jsonify(ack_payload)
