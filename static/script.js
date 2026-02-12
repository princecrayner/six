document.addEventListener("DOMContentLoaded", () => {

  const feed = document.getElementById("feed");
  const fileInput = document.getElementById("fileInput");
  const authBox = document.getElementById("authBox");

  /* ---------- LOAD VIDEOS ---------- */
  async function load() {
    let res = await fetch("/videos");
    let videos = await res.json();

    feed.innerHTML = "";

    videos.forEach(v => {
      feed.innerHTML += `
        <div class="card">
          <video src="/uploads/${v.file}" controls
            onplay="view(${v.id})"></video>

          <p>
            👁 <span id="v${v.id}">${v.views}</span>
            ❤️ <span id="l${v.id}">${v.likes}</span>
          </p>

          <button onclick="like(${v.id})">Like</button>
          <button onclick="del(${v.id})">Delete</button>

          <input placeholder="Comment"
                 onkeydown="comment(event, ${v.id})">
          <div id="c${v.id}"></div>
        </div>
      `;

      loadComments(v.id);
    });
  }

  /* ---------- UPLOAD ---------- */
  window.startUpload = function () {
    fileInput.value = "";
    fileInput.click();
  };

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    const title = prompt("Enter video title");
    if (!title) return;

    const data = new FormData();
    data.append("video", file);
    data.append("title", title);

    const res = await fetch("/upload", {
      method: "POST",
      body: data
    });

    const json = await res.json();

    if (json.error) {
      alert("You must be logged in to upload");
      return;
    }

    load();
  });

  /* ---------- AUTH UI ---------- */
  window.toggleAuth = function () {
    authBox.style.display =
      authBox.style.display === "flex" ? "none" : "flex";
  };

  window.login = async function () {
    let u = document.getElementById("username").value;
    let p = document.getElementById("password").value;

    let r = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p })
    });

    let j = await r.json();
    if (j.ok) {
      alert("Logged in");
      authBox.style.display = "none";
    } else {
      alert("Login failed");
    }
  };

  window.register = async function () {
    let u = document.getElementById("username").value;
    let p = document.getElementById("password").value;

    let r = await fetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p })
    });

    let j = await r.json();
    if (j.ok) {
      alert("Registered. Now login.");
    } else {
      alert("Username already exists");
    }
  };

    function closeAuth() {
  const authBox = document.getElementById("authBox");
  authBox.style.display = "none";
}

  /* ---------- LIKE ---------- */
  window.like = async function (id) {
    let r = await fetch("/like/" + id, { method: "POST" });
    let j = await r.json();
    document.getElementById("l" + id).innerText = j.likes;
  };

  /* ---------- VIEW ---------- */
  window.view = async function (id) {
    let r = await fetch("/view/" + id, { method: "POST" });
    let j = await r.json();
    document.getElementById("v" + id).innerText = j.views;
  };

  /* ---------- DELETE ---------- */
  window.del = async function (id) {
    await fetch("/delete/" + id, { method: "POST" });
    load();
  };

  /* ---------- COMMENTS ---------- */
  window.comment = async function (e, id) {
    if (e.key === "Enter") {
      await fetch("/comment/" + id, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: e.target.value })
      });
      e.target.value = "";
      loadComments(id);
    }
  };

  async function loadComments(id) {
    let r = await fetch("/comments/" + id);
    let data = await r.json();
    document.getElementById("c" + id).innerHTML =
      data.map(x => `<p><b>${x[0]}:</b> ${x[1]}</p>`).join("");
  }

  load();
});
