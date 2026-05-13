from __future__ import annotations

import os
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .common import success_response


router = APIRouter()


class ReverseGeocodeRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


def _compose_human_readable(address_component: dict, formatted_address: str, poi_name: str) -> str:
    province = str(address_component.get("province") or "").strip()
    city = address_component.get("city")
    if isinstance(city, list):
        city = ""
    city = str(city or "").strip()
    district = str(address_component.get("district") or "").strip()
    township = str(address_component.get("township") or "").strip()

    street_info = address_component.get("streetNumber") or {}
    street = str(street_info.get("street") or "").strip()
    number = str(street_info.get("number") or "").strip()

    parts = [part for part in [province, city, district, township] if part]
    line = "".join(parts)
    road = "".join([part for part in [street, number] if part])
    if road and road not in line:
        line = line + road
    if poi_name and poi_name not in line:
        line = (line + " " + poi_name).strip()
    if not line:
        line = formatted_address.strip()
    return line


async def _reverse_geocode_with_amap(latitude: float, longitude: float) -> Optional[dict]:
    api_key = os.getenv("AMAP_WEB_API_KEY", "").strip()
    if not api_key:
        return None

    url = "https://restapi.amap.com/v3/geocode/regeo"
    params = {
        "key": api_key,
        "location": f"{longitude:.6f},{latitude:.6f}",
        "extensions": "all",
        "radius": "1000",
        "roadlevel": "0",
    }

    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    if str(payload.get("status")) != "1":
        info = payload.get("info") or "逆地理编码失败"
        raise HTTPException(status_code=502, detail=f"逆地理编码失败：{info}")

    regeocode = payload.get("regeocode") or {}
    address_component = regeocode.get("addressComponent") or {}
    pois = regeocode.get("pois") or []
    poi_name = ""
    if isinstance(pois, list) and pois:
        first_poi = pois[0] or {}
        poi_name = str(first_poi.get("name") or "").strip()

    formatted_address = str(regeocode.get("formatted_address") or "").strip()
    human_readable = _compose_human_readable(address_component, formatted_address, poi_name)

    return {
        "provider": "amap",
        "formatted_address": formatted_address,
        "human_readable": human_readable,
        "poi_name": poi_name,
        "address_component": address_component,
    }


@router.post("/api/location/reverse-geocode")
async def reverse_geocode(payload: ReverseGeocodeRequest, request: Request):
    """把浏览器定位坐标转成更适合填写的人类可读地址。"""
    try:
        geocode = await _reverse_geocode_with_amap(payload.latitude, payload.longitude)
        fallback = f"定位坐标({payload.latitude:.5f}, {payload.longitude:.5f})"

        if not geocode:
            return success_response(
                {
                    "available": False,
                    "provider": None,
                    "human_readable": fallback,
                    "formatted_address": fallback,
                    "fallback": True,
                    "message": "未配置逆地理编码服务，已回退为坐标文本。",
                },
                request=request,
            )

        return success_response(
            {
                "available": True,
                "provider": geocode["provider"],
                "human_readable": geocode["human_readable"] or fallback,
                "formatted_address": geocode["formatted_address"] or geocode["human_readable"] or fallback,
                "poi_name": geocode["poi_name"],
                "address_component": geocode["address_component"],
                "fallback": False,
            },
            request=request,
        )
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"逆地理编码服务请求失败: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"逆地理编码失败: {str(exc)}")
