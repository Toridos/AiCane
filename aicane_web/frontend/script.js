async function upload(){
    let file = document.getElementById("fileInput").files[0];
    let form = new FormData();
    form.append("file", file);

    let res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: form
    });

    console.log(await res.json());
}

async function processMap(){
    let filename = document.getElementById("fileInput").files[0].name;

    let res = await fetch("http://localhost:8000/process-map?filename="+filename, {
        method: "POST"
    });

    document.getElementById("logBox").innerText = JSON.stringify(await res.json(), null, 2);
}

async function navigate(){
    let res = await fetch("http://localhost:8000/navigate?room=115");
    document.getElementById("logBox").innerText = JSON.stringify(await res.json(), null, 2);
}
