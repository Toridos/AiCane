let canvas = document.getElementById("gridCanvas");
let ctx = canvas.getContext("2d");

let gridW = 2667;  // grid 실제 너비
let gridH = 1500;  // grid 실제 높이

async function loadGrid() {
    const response = await fetch("http://127.0.0.1:8000/grid/image");
    const blob = await response.blob();
    const img = await createImageBitmap(blob);

    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
}

async function drawPath() {
    let room = document.getElementById("roomInput").value;

    const data = await fetch(`http://127.0.0.1:8000/path?room=${room}`)
        .then(r => r.json());

    let path = data.path;

    if (!path || path.length === 0) {
        alert("경로 없음");
        return;
    }

    let scaleX = canvas.width / gridW;
    let scaleY = canvas.height / gridH;

    ctx.fillStyle = "red";

    path.forEach(([x, y]) => {
        let px = x * scaleX;
        let py = y * scaleY;
        ctx.fillRect(px, py, 3, 3);
    });
}

loadGrid();
