(function () {
  var POLL_INTERVAL_MS = 1500;

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function renderIdle(container) {
    container.dataset.status = "idle";
    container.className = "fetch-progress state state-empty";
    container.removeAttribute("role");
    container.innerHTML = "";
    container.appendChild(el("p", null, "아직 실행 이력이 없습니다. 위 버튼을 눌러 수집을 시작하세요."));
  }

  function renderRunning(container, snapshot) {
    container.dataset.status = "running";
    container.className = "fetch-progress fetch-progress--panel";
    container.removeAttribute("role");
    container.innerHTML = "";

    var summary = el(
      "p",
      "fetch-progress__summary",
      "수집 진행 중 — 글 완료 " + snapshot.articles.done + "건 / 실패 " + snapshot.articles.failed + "건"
    );
    container.appendChild(el("div", "spinner"));
    container.appendChild(summary);

    var feedNames = Object.keys(snapshot.feeds);
    if (feedNames.length > 0) {
      var list = el("ul", "fetch-feed-list");
      feedNames.forEach(function (name) {
        var item = el("li", "fetch-feed-list__item");
        item.appendChild(el("span", null, name));
        item.appendChild(
          el("span", "fetch-feed-status fetch-feed-status--running", snapshot.feeds[name].status)
        );
        list.appendChild(item);
      });
      container.appendChild(list);
    }
  }

  function renderDone(container, snapshot) {
    container.dataset.status = "done";
    container.className = "fetch-progress fetch-progress--panel";
    container.removeAttribute("role");
    container.innerHTML = "";

    var report = snapshot.report || {};
    var articles = report.articles || {};
    var feedsReport = report.feeds || {};

    container.appendChild(el("p", null, "수집이 완료되었습니다."));
    container.appendChild(
      el(
        "p",
        "fetch-progress__summary",
        "글 성공 " + (articles.succeeded || 0) + "건 / 실패 " + (articles.failed || 0) +
          "건, 피드 성공 " + (feedsReport.succeeded || 0) + "건 / 실패 " + (feedsReport.failed || 0) + "건"
      )
    );

    var failures = (articles.failures || []).concat(feedsReport.failures || []);
    if (failures.length > 0) {
      var list = el("ul", "fetch-report__failures");
      failures.forEach(function (failure) {
        list.appendChild(el("li", null, typeof failure === "string" ? failure : JSON.stringify(failure)));
      });
      container.appendChild(list);
    }
  }

  function renderError(container, snapshot) {
    container.dataset.status = "error";
    container.className = "fetch-progress state state-error";
    container.setAttribute("role", "alert");
    container.innerHTML = "";
    container.appendChild(el("p", null, snapshot.error || "수집 중 오류가 발생했습니다."));
  }

  function render(container, button, snapshot) {
    if (snapshot.status === "running") {
      renderRunning(container, snapshot);
      button.disabled = true;
    } else if (snapshot.status === "done") {
      renderDone(container, snapshot);
      button.disabled = false;
    } else if (snapshot.status === "error") {
      renderError(container, snapshot);
      button.disabled = false;
    } else {
      renderIdle(container);
      button.disabled = false;
    }
  }

  function poll(container, button) {
    fetch("/fetch/progress")
      .then(function (response) {
        return response.json();
      })
      .then(function (snapshot) {
        render(container, button, snapshot);
        if (snapshot.status === "running") {
          window.setTimeout(function () {
            poll(container, button);
          }, POLL_INTERVAL_MS);
        }
      })
      .catch(function () {
        window.setTimeout(function () {
          poll(container, button);
        }, POLL_INTERVAL_MS);
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("fetch-trigger-form");
    var button = document.getElementById("fetch-trigger-button");
    var container = document.getElementById("fetch-progress");
    if (!form || !button || !container) {
      return;
    }

    poll(container, button);

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      button.disabled = true;
      fetch("/fetch", { method: "POST" })
        .then(function () {
          poll(container, button);
        })
        .catch(function () {
          button.disabled = false;
        });
    });
  });
})();
