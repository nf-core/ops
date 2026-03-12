(function polyfill() {
  const relList = document.createElement("link").relList;
  if (relList && relList.supports && relList.supports("modulepreload")) {
    return;
  }
  for (const link of document.querySelectorAll('link[rel="modulepreload"]')) {
    processPreload(link);
  }
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type !== "childList") {
        continue;
      }
      for (const node of mutation.addedNodes) {
        if (node.tagName === "LINK" && node.rel === "modulepreload")
          processPreload(node);
      }
    }
  }).observe(document, { childList: true, subtree: true });
  function getFetchOpts(link) {
    const fetchOpts = {};
    if (link.integrity) fetchOpts.integrity = link.integrity;
    if (link.referrerPolicy) fetchOpts.referrerPolicy = link.referrerPolicy;
    if (link.crossOrigin === "use-credentials")
      fetchOpts.credentials = "include";
    else if (link.crossOrigin === "anonymous") fetchOpts.credentials = "omit";
    else fetchOpts.credentials = "same-origin";
    return fetchOpts;
  }
  function processPreload(link) {
    if (link.ep)
      return;
    link.ep = true;
    const fetchOpts = getFetchOpts(link);
    fetch(link.href, fetchOpts);
  }
})();
console.log("nf-core hackathon map script loaded");
let currentPopup = void 0;
function closePopup() {
  if (currentPopup !== void 0) {
    currentPopup.close();
    currentPopup = void 0;
  }
}
WA.onInit().then(() => {
  console.log("nf-core hackathon scripting API ready");
  WA.chat.sendChatMessage(
    "Welcome to the nf-core hackathon! Need help? Check out https://nf-co.re/events/2026/hackathon-march-2026",
    "nf-core bot"
  );
  WA.room.area.onEnter("needHelp").subscribe(() => {
    currentPopup = WA.ui.openPopup("needHelpPopup", "Need help with nf-core?", [
      {
        label: "Slack",
        className: "primary",
        callback: () => {
          WA.nav.openTab("https://nf-co.re/join/slack");
          closePopup();
        }
      },
      {
        label: "Documentation",
        className: "normal",
        callback: () => {
          WA.nav.openTab("https://nf-co.re/docs");
          closePopup();
        }
      },
      {
        label: "GitHub",
        className: "normal",
        callback: () => {
          WA.nav.openTab("https://github.com/nf-core");
          closePopup();
        }
      }
    ]);
  });
  WA.room.area.onLeave("needHelp").subscribe(closePopup);
  WA.room.area.onEnter("followUs").subscribe(() => {
    currentPopup = WA.ui.openPopup("followUsPopup", "Connect with nf-core!", [
      {
        label: "Mastodon",
        className: "primary",
        callback: () => {
          WA.nav.openTab("https://mstdn.science/@nf_core");
          closePopup();
        }
      },
      {
        label: "Bluesky",
        className: "normal",
        callback: () => {
          WA.nav.openTab("https://bsky.app/profile/nf-co.re");
          closePopup();
        }
      },
      {
        label: "YouTube",
        className: "normal",
        callback: () => {
          WA.nav.openTab("https://www.youtube.com/@nf-core");
          closePopup();
        }
      },
      {
        label: "LinkedIn",
        className: "normal",
        callback: () => {
          WA.nav.openTab("https://www.linkedin.com/company/nf-core");
          closePopup();
        }
      }
    ]);
  });
  WA.room.area.onLeave("followUs").subscribe(closePopup);
  WA.room.area.onEnter("hackathonInfo").subscribe(() => {
    currentPopup = WA.ui.openPopup("hackathonInfoPopup", "Hackathon Resources", [
      {
        label: "Event Info",
        className: "primary",
        callback: () => {
          WA.nav.openTab("https://nf-co.re/events/2026/hackathon-march-2026");
          closePopup();
        }
      },
      {
        label: "Projects",
        className: "normal",
        callback: () => {
          WA.nav.openTab("https://nf-co.re/events/2026/hackathon-march-2026#list-of-projects");
          closePopup();
        }
      },
      {
        label: "Code of Conduct",
        className: "normal",
        callback: () => {
          WA.nav.openTab("https://nf-co.re/code_of_conduct");
          closePopup();
        }
      }
    ]);
  });
  WA.room.area.onLeave("hackathonInfo").subscribe(closePopup);
}).catch((e) => console.error("Script init error:", e));
//# sourceMappingURL=main.js.map
