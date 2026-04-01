/**
 * Сбор технических данных браузера (как на auth.html) для отправки на бэкенд
 * при явном согласии пользователя.
 */
(function () {
  const API_BASE = typeof window.LUXARY_API_BASE === "string" ? window.LUXARY_API_BASE : "";

  function getBrowserInfo() {
    const userAgent = navigator.userAgent;
    const browserRegex =
      /(firefox|chrome|safari|edge|msie|trident)\s*\/?\s*([0-9.]+)/i;
    const browserMatch = userAgent.match(browserRegex);

    let browser = "Unknown";
    let browserVersion = "Unknown";

    if (browserMatch) {
      browser = browserMatch[1].toLowerCase();
      browserVersion = browserMatch[2];
    } else if (userAgent.includes("Firefox")) {
      browser = "Firefox";
      browserVersion = userAgent.split("Firefox/")[1];
    } else if (userAgent.includes("Chrome")) {
      browser = "Chrome";
      browserVersion = userAgent.split("Chrome/")[1].split(" ")[0];
    } else if (
      userAgent.includes("Safari") &&
      !userAgent.includes("Chrome")
    ) {
      browser = "Safari";
      browserVersion = userAgent.split("Version/")[1] || "Unknown";
    } else if (userAgent.includes("Edge")) {
      browser = "Edge";
      browserVersion = userAgent.split("Edge/")[1];
    }

    let os = "Unknown";
    let osVersion = "Unknown";
    if (userAgent.includes("Windows NT 10.0")) {
      os = "Windows";
      osVersion = "10";
    } else if (userAgent.includes("Windows NT 6.3")) {
      os = "Windows";
      osVersion = "8.1";
    } else if (userAgent.includes("Windows NT 6.2")) {
      os = "Windows";
      osVersion = "8";
    } else if (userAgent.includes("Windows NT 6.1")) {
      os = "Windows";
      osVersion = "7";
    } else if (userAgent.includes("Mac OS X")) {
      os = "macOS";
      osVersion = userAgent
        .split("Mac OS X ")[1]
        .replace(/_/g, ".")
        .split(")")[0];
    } else if (userAgent.includes("Linux")) {
      os = "Linux";
      osVersion = "Unknown";
    } else if (userAgent.includes("Android")) {
      os = "Android";
      osVersion = userAgent.split("Android ")[1].split(";")[0];
    } else if (
      userAgent.includes("iOS") ||
      userAgent.includes("iPhone") ||
      userAgent.includes("iPad")
    ) {
      os = "iOS";
      osVersion = userAgent.split("OS ")[1]?.split(" ")[0] || "Unknown";
    }

    let deviceType = "Desktop";
    if (
      /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
        userAgent,
      )
    ) {
      deviceType =
        /iPad|iPhone|iPod/.test(userAgent) && !window.MSStream
          ? "iOS"
          : "Mobile";
    }

    return {
      browser,
      browser_version: browserVersion,
      os,
      os_version: osVersion,
      device_type: deviceType,
      platform: navigator.platform || "Unknown",
      user_agent: userAgent,
    };
  }

  function getScreenInfo() {
    return {
      screen_resolution: `${screen.width}x${screen.height}`,
      screen_color_depth: `${screen.colorDepth}-bit`,
      screen_avail_resolution: `${screen.availWidth}x${screen.availHeight}`,
      screen_pixel_depth: screen.pixelDepth,
      device_pixel_ratio: window.devicePixelRatio,
    };
  }

  function getLanguageInfo() {
    return {
      language: navigator.language || "Unknown",
      languages: Array.isArray(navigator.languages)
        ? navigator.languages.join(",")
        : navigator.language,
    };
  }

  function getTimezoneInfo() {
    try {
      return {
        timezone:
          Intl.DateTimeFormat().resolvedOptions().timeZone || "Unknown",
        timezone_offset: new Date().getTimezoneOffset(),
      };
    } catch (e) {
      return { timezone: "Unknown", timezone_offset: "Unknown" };
    }
  }

  function getHardwareInfo() {
    return {
      cpu_cores: navigator.hardwareConcurrency || "Unknown",
      device_memory: navigator.deviceMemory
        ? `${navigator.deviceMemory} GB`
        : "Unknown",
      hardware_concurrency: navigator.hardwareConcurrency,
      cookie_enabled: navigator.cookieEnabled,
      do_not_track: navigator.doNotTrack || "Unknown",
      java_enabled: navigator.javaEnabled ? navigator.javaEnabled() : false,
    };
  }

  async function getNetworkInfo() {
    const networkData = {};
    if (navigator.connection) {
      networkData.connection_type =
        navigator.connection.effectiveType || "Unknown";
      networkData.connection_downlink =
        navigator.connection.downlink || "Unknown";
      networkData.connection_rtt = navigator.connection.rtt || "Unknown";
      networkData.connection_save_data =
        navigator.connection.saveData || false;
    }
    try {
      const res = await fetch(`${API_BASE}/api/auth/ip`);
      const data = await res.json();
      networkData.ip_address = data.ip || "Unknown";
    } catch (e) {
      networkData.ip_address = "Unknown";
    }
    return networkData;
  }

  function getGPUInfo() {
    let gpu = "Unknown";
    let vendor = "Unknown";
    try {
      const canvas = document.createElement("canvas");
      const gl =
        canvas.getContext("webgl") ||
        canvas.getContext("experimental-webgl");
      if (gl) {
        const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
        if (debugInfo) {
          gpu =
            gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || "Unknown";
          vendor =
            gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || "Unknown";
        }
      }
    } catch (e) {
      gpu = "Unknown";
      vendor = "Unknown";
    }
    return { gpu, vendor };
  }

  function getTouchSupport() {
    let touchSupport = "No";
    if (
      "ontouchstart" in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0
    ) {
      touchSupport = `Yes (${navigator.maxTouchPoints || navigator.msMaxTouchPoints || 0} points)`;
    }
    return { touch_support: touchSupport };
  }

  function getMemoryInfo() {
    if (performance.memory) {
      return {
        memory_used:
          Math.round(performance.memory.usedJSHeapSize / 1048576) + " MB",
        memory_total:
          Math.round(performance.memory.totalJSHeapSize / 1048576) + " MB",
        memory_limit:
          Math.round(performance.memory.jsHeapSizeLimit / 1048576) + " MB",
      };
    }
    return {
      memory_used: "Unknown",
      memory_total: "Unknown",
      memory_limit: "Unknown",
    };
  }

  function getPluginsInfo() {
    const plugins = [];
    if (navigator.plugins) {
      for (let i = 0; i < navigator.plugins.length; i++) {
        plugins.push(navigator.plugins[i].name);
      }
    }
    return { plugins: plugins.join(", ") };
  }

  async function collectAllDeviceData() {
    const browserInfo = getBrowserInfo();
    const screenInfo = getScreenInfo();
    const languageInfo = getLanguageInfo();
    const timezoneInfo = getTimezoneInfo();
    const hardwareInfo = getHardwareInfo();
    const networkInfo = await getNetworkInfo();
    const gpuInfo = getGPUInfo();
    const touchSupport = getTouchSupport();
    const memoryInfo = getMemoryInfo();
    const pluginsInfo = getPluginsInfo();

    let canvasFingerprint = "Unknown";
    try {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      ctx.textBaseline = "top";
      ctx.font = "14px Arial";
      ctx.fillText("Canvas Fingerprint", 2, 2);
      canvasFingerprint = canvas.toDataURL().slice(-50);
    } catch (e) {
      canvasFingerprint = "Unknown";
    }

    let audioFingerprint = "Unknown";
    try {
      const audioContext = new (
        window.AudioContext || window.webkitAudioContext
      )();
      audioFingerprint = audioContext.state;
      audioContext.close();
    } catch (e) {
      audioFingerprint = "Unknown";
    }

    let webrtcIPs = [];
    try {
      const peerConnection = new RTCPeerConnection({ iceServers: [] });
      peerConnection.createDataChannel("");
      peerConnection
        .createOffer()
        .then((offer) => peerConnection.setLocalDescription(offer));
      peerConnection.onicecandidate = (ice) => {
        if (ice && ice.candidate) {
          const ipMatch = /([0-9]{1,3}(\.[0-9]{1,3}){3})/.exec(
            ice.candidate.candidate,
          );
          if (ipMatch) webrtcIPs.push(ipMatch[1]);
        }
      };
    } catch (e) {
      webrtcIPs = [];
    }

    return {
      ...browserInfo,
      ...screenInfo,
      ...languageInfo,
      ...timezoneInfo,
      ...hardwareInfo,
      ...networkInfo,
      ...gpuInfo,
      ...touchSupport,
      ...memoryInfo,
      ...pluginsInfo,
      canvas_fingerprint: canvasFingerprint,
      audio_fingerprint: audioFingerprint,
      webrtc_ips: webrtcIPs.join(","),
      collected_at: new Date().toISOString(),
    };
  }

  function getLuxaryLocalStorageSnapshot() {
    const out = {};
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && k.startsWith("luxary_")) {
          out[k] = localStorage.getItem(k);
        }
      }
    } catch (e) {
      out.error = String(e);
    }
    return out;
  }

  function getNavigatorExtra() {
    return {
      vendor: navigator.vendor,
      maxTouchPoints: navigator.maxTouchPoints,
      pdfViewerEnabled: navigator.pdfViewerEnabled,
      webdriver: navigator.webdriver,
      onLine: navigator.onLine,
      document_cookie_length: document.cookie ? document.cookie.length : 0,
      window_size: `${window.innerWidth}x${window.innerHeight}`,
      location_href: window.location.href,
      location_pathname: window.location.pathname,
    };
  }

  window.collectAllDeviceData = collectAllDeviceData;
  window.getLuxaryLocalStorageSnapshot = getLuxaryLocalStorageSnapshot;
  window.getNavigatorExtra = getNavigatorExtra;
})();
