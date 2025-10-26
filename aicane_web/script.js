let map, startMarker, endMarker, startPos, endPos;
const SERVER_URL = "http://192.168.0.10:5000/route"; // Flask 서버 IP

function initMap() {
  const cbnu = { lat: 36.6321, lng: 127.4599 };
  map = new google.maps.Map(document.getElementById("map"), {
    center: cbnu, zoom: 17,
  });

  map.addListener("click", (event) => {
    if (!startMarker) {
      startPos = event.latLng;
      startMarker = new google.maps.Marker({
        position: startPos, map: map, label: "S", title: "출발지",
      });
    } else if (!endMarker) {
      endPos = event.latLng;
      endMarker = new google.maps.Marker({
        position: endPos, map: map, label: "E", title: "도착지",
      });
    } else {
      startMarker.setMap(null);
      endMarker.setMap(null);
      startMarker = endMarker = null;
      startPos = endPos = null;
    }
  });
}

async function sendRoute() {
  if (!startPos || !endPos) {
    alert("출발지와 도착지를 모두 선택하세요!");
    return;
  }

  const routeData = {
    route_id: "R" + Date.now(),
    start: { lat: startPos.lat(), lng: startPos.lng() },
    destination: { lat: endPos.lat(), lng: endPos.lng() },
    path: [
      { lat: startPos.lat(), lng: startPos.lng() },
      { lat: endPos.lat(), lng: endPos.lng() }
    ],
    options: { avoid_stairs: true, mode: "walking" }
  };

  try {
    const res = await fetch(SERVER_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(routeData),
    });
    if (res.ok) alert("✅ 경로 전송 완료 — 로봇이 이동을 시작합니다!");
    else alert("❌ 서버 오류: " + res.status);
  } catch (err) {
    alert("⚠️ 전송 실패: " + err.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  document.getElementById("sendBtn").addEventListener("click", sendRoute);
});
