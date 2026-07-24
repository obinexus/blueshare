const elements = {
  servicePill: document.querySelector("#service-pill"),
  serviceStatus: document.querySelector("#service-status"),
  joinCard: document.querySelector("#join-card"),
  joinForm: document.querySelector("#join-form"),
  joinButton: document.querySelector("#join-button"),
  formError: document.querySelector("#form-error"),
  peerName: document.querySelector("#peer-name"),
  pairingCode: document.querySelector("#pairing-code"),
  positionU: document.querySelector("#position-u"),
  positionV: document.querySelector("#position-v"),
  positionW: document.querySelector("#position-w"),
  dashboard: document.querySelector("#dashboard"),
  mmukoState: document.querySelector("#mmuko-state"),
  connectedCount: document.querySelector("#connected-count"),
  lastHeartbeat: document.querySelector("#last-heartbeat"),
  topologyNote: document.querySelector("#topology-note"),
  peerGrid: document.querySelector("#peer-grid"),
  heartbeatButton: document.querySelector("#heartbeat-button"),
  leaveButton: document.querySelector("#leave-button"),
  liveU: document.querySelector("#live-u"),
  liveV: document.querySelector("#live-v"),
  liveW: document.querySelector("#live-w"),
  mediaFile: document.querySelector("#media-file"),
  mediaUploadButton: document.querySelector("#media-upload-button"),
  mediaMessage: document.querySelector("#media-message"),
  mediaTitle: document.querySelector("#media-title"),
  mediaState: document.querySelector("#media-state"),
  roomAudio: document.querySelector("#room-audio"),
  mediaEnableButton: document.querySelector("#media-enable-button"),
  mediaPlayButton: document.querySelector("#media-play-button"),
  mediaPauseButton: document.querySelector("#media-pause-button"),
  mediaStopButton: document.querySelector("#media-stop-button"),
  mediaSeek: document.querySelector("#media-seek"),
  mediaPosition: document.querySelector("#media-position"),
  mediaDuration: document.querySelector("#media-duration"),
  localVolume: document.querySelector("#local-volume"),
  eventList: document.querySelector("#event-list"),
  clearEvents: document.querySelector("#clear-events"),
};

function createClientId() {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return `peer-${Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("")}`;
}

const runtime = {
  clientId: localStorage.getItem("blueshare.clientId") || createClientId(),
  session: null,
  positionSeq: Number(sessionStorage.getItem("blueshare.positionSeq") || "0"),
  timer: null,
  heartbeatInFlight: false,
  mediaTimer: null,
  mediaPollInFlight: false,
  mediaId: null,
  mediaRevision: 0,
  mediaState: null,
  audioEnabled: false,
};

localStorage.setItem("blueshare.clientId", runtime.clientId);
elements.peerName.value = localStorage.getItem("blueshare.peerName") || "";
elements.localVolume.value = localStorage.getItem("blueshare.localVolume") || "0.8";
elements.roomAudio.volume = Number(elements.localVolume.value);

try {
  const savedPosition = JSON.parse(localStorage.getItem("blueshare.position"));
  if ([savedPosition?.u, savedPosition?.v, savedPosition?.w].every(Number.isFinite)) {
    for (const [joinInput, liveInput, value] of [
      [elements.positionU, elements.liveU, savedPosition.u],
      [elements.positionV, elements.liveV, savedPosition.v],
      [elements.positionW, elements.liveW, savedPosition.w],
    ]) {
      joinInput.value = String(value);
      liveInput.value = String(value);
    }
  }
} catch {
  localStorage.removeItem("blueshare.position");
}

function event(message) {
  const item = document.createElement("li");
  const timestamp = document.createElement("time");
  timestamp.dateTime = new Date().toISOString();
  timestamp.textContent = new Date().toLocaleTimeString();
  const text = document.createElement("span");
  text.textContent = message;
  item.append(timestamp, text);
  elements.eventList.prepend(item);
  while (elements.eventList.children.length > 12) {
    elements.eventList.lastElementChild.remove();
  }
}

function setServiceState(state, text) {
  elements.servicePill.dataset.state = state;
  elements.serviceStatus.textContent = text;
}

async function api(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  const body = await response.json().catch(() => ({ message: `HTTP ${response.status}` }));
  if (!response.ok) {
    const error = new Error(body.message || `HTTP ${response.status}`);
    error.code = body.error;
    error.status = response.status;
    throw error;
  }
  return body;
}

function authenticatedPayload(extra = {}) {
  if (!runtime.session) throw new Error("Join BlueShare before using the media room");
  return {
    peer_id: runtime.session.peerId,
    session_token: runtime.session.sessionToken,
    ...extra,
  };
}

function formatMediaTime(value) {
  if (!Number.isFinite(value) || value < 0) return "0:00";
  const seconds = Math.floor(value % 60).toString().padStart(2, "0");
  return `${Math.floor(value / 60)}:${seconds}`;
}

function effectiveMediaDuration() {
  if (Number.isFinite(elements.roomAudio.duration) && elements.roomAudio.duration > 0) {
    return elements.roomAudio.duration;
  }
  const declared = runtime.mediaState?.duration_seconds;
  return Number.isFinite(declared) && declared > 0 ? declared : 0;
}

function updateMediaTimeline(position = elements.roomAudio.currentTime) {
  const duration = effectiveMediaDuration();
  const safePosition = Number.isFinite(position) ? Math.max(0, position) : 0;
  elements.mediaPosition.textContent = formatMediaTime(safePosition);
  elements.mediaDuration.textContent = formatMediaTime(duration);
  elements.mediaSeek.value = duration > 0
    ? String(Math.min(1000, Math.round((safePosition / duration) * 1000)))
    : "0";
}

function setMediaControls(enabled) {
  elements.mediaPlayButton.disabled = !enabled;
  elements.mediaPauseButton.disabled = !enabled;
  elements.mediaStopButton.disabled = !enabled;
  elements.mediaSeek.disabled = !enabled;
}

function resetMediaPlayer() {
  runtime.mediaId = null;
  runtime.mediaRevision = 0;
  runtime.mediaState = null;
  elements.roomAudio.pause();
  elements.roomAudio.removeAttribute("src");
  elements.roomAudio.load();
  elements.mediaTitle.textContent = "No shared track";
  elements.mediaState.textContent = "EMPTY";
  elements.mediaState.dataset.state = "EMPTY";
  elements.mediaMessage.textContent = "No room audio has been selected.";
  setMediaControls(false);
  updateMediaTimeline(0);
}

function synchronizeAudioPosition(target) {
  if (!Number.isFinite(target) || elements.roomAudio.readyState === 0) return;
  if (Math.abs(elements.roomAudio.currentTime - target) > 0.65) {
    try {
      elements.roomAudio.currentTime = target;
    } catch {
      // The next media-state poll retries after metadata is available.
    }
  }
}

function renderMedia(media) {
  if (!media || !media.media_id) {
    if (runtime.mediaId) resetMediaPlayer();
    return;
  }

  const changedTrack = runtime.mediaId !== media.media_id;
  const changedRevision = runtime.mediaRevision !== media.revision;
  runtime.mediaId = media.media_id;
  runtime.mediaState = media;
  runtime.mediaRevision = media.revision;

  if (changedTrack) {
    elements.roomAudio.src = media.stream_url;
    elements.roomAudio.load();
    elements.mediaTitle.textContent = media.filename;
    elements.mediaMessage.textContent = `${(media.size_bytes / (1024 * 1024)).toFixed(2)} MiB shared by ${media.updated_by?.name || "a peer"}.`;
    event(`Room track available: ${media.filename}`);
  }

  elements.mediaState.textContent = media.status;
  elements.mediaState.dataset.state = media.status;
  setMediaControls(true);
  synchronizeAudioPosition(media.position_seconds);
  updateMediaTimeline(media.position_seconds);

  if (media.status === "PLAYING") {
    if (runtime.audioEnabled) {
      elements.roomAudio.play().catch(() => {
        runtime.audioEnabled = false;
        elements.mediaMessage.textContent = "Playback needs permission. Select Enable this speaker.";
      });
    } else {
      elements.roomAudio.pause();
      elements.mediaMessage.textContent = "The room is playing. Select Enable this speaker to hear it here.";
    }
  } else {
    elements.roomAudio.pause();
    if (changedRevision && !changedTrack) {
      elements.mediaMessage.textContent = media.status === "READY"
        ? "The room is stopped and ready at the beginning."
        : `The room is paused at ${formatMediaTime(media.position_seconds)}.`;
    }
  }

  if (changedRevision && !changedTrack && media.updated_by?.name) {
    event(`${media.updated_by.name} changed room transport to ${media.status}`);
  }
}

async function pollMedia() {
  if (!runtime.session || runtime.mediaPollInFlight) return;
  runtime.mediaPollInFlight = true;
  try {
    const response = await api("/api/media/state", authenticatedPayload());
    renderMedia(response.media);
  } catch (error) {
    if (error.status === 401 || error.code === "peer_not_active") return;
    elements.mediaMessage.textContent = `Media state unavailable: ${error.message}`;
  } finally {
    runtime.mediaPollInFlight = false;
  }
}

function startMediaPolling() {
  if (runtime.mediaTimer) clearInterval(runtime.mediaTimer);
  runtime.mediaTimer = setInterval(pollMedia, 750);
  pollMedia();
}

function inferredAudioType(file) {
  if (file.type?.startsWith("audio/")) return file.type;
  const extension = file.name.split(".").pop()?.toLowerCase();
  return ({
    mp3: "audio/mpeg",
    m4a: "audio/mp4",
    mp4: "audio/mp4",
    wav: "audio/wav",
    ogg: "audio/ogg",
    opus: "audio/ogg",
    flac: "audio/flac",
    webm: "audio/webm",
    aac: "audio/aac",
  })[extension] || "";
}

function inspectAudioDuration(file) {
  return new Promise((resolve) => {
    const objectUrl = URL.createObjectURL(file);
    const probe = document.createElement("audio");
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      URL.revokeObjectURL(objectUrl);
      probe.removeAttribute("src");
      resolve(Number.isFinite(value) && value > 0 ? value : null);
    };
    const timeout = setTimeout(() => finish(null), 5000);
    probe.preload = "metadata";
    probe.addEventListener("loadedmetadata", () => {
      clearTimeout(timeout);
      finish(probe.duration);
    }, { once: true });
    probe.addEventListener("error", () => {
      clearTimeout(timeout);
      finish(null);
    }, { once: true });
    probe.src = objectUrl;
  });
}

async function uploadMedia() {
  const file = elements.mediaFile.files[0];
  if (!file) {
    elements.mediaMessage.textContent = "Choose an audio file first.";
    return;
  }
  const contentType = inferredAudioType(file);
  if (!contentType) {
    elements.mediaMessage.textContent = "The selected file does not have a supported audio type.";
    return;
  }

  elements.mediaUploadButton.disabled = true;
  elements.mediaMessage.textContent = `Uploading ${file.name}…`;
  try {
    const session = authenticatedPayload();
    const duration = await inspectAudioDuration(file);
    const headers = {
      "Content-Type": contentType,
      "X-BlueShare-Peer-Id": session.peer_id,
      "X-BlueShare-Session-Token": session.session_token,
      "X-BlueShare-Filename": encodeURIComponent(file.name),
    };
    if (duration !== null) headers["X-BlueShare-Duration"] = String(duration);
    const response = await fetch("/api/media/upload", {
      method: "POST",
      headers,
      body: file,
      cache: "no-store",
    });
    const body = await response.json().catch(() => ({ message: `HTTP ${response.status}` }));
    if (!response.ok) throw Object.assign(new Error(body.message), { status: response.status, code: body.error });
    renderMedia(body.media);
    elements.mediaMessage.textContent = `${file.name} is ready for ${elements.connectedCount.textContent} peer(s).`;
    event(`Uploaded room track: ${file.name}`);
  } catch (error) {
    elements.mediaMessage.textContent = `Upload failed: ${error.message}`;
    event(`Media upload failed: ${error.message}`);
  } finally {
    elements.mediaUploadButton.disabled = false;
  }
}

async function controlMedia(action, positionSeconds = null) {
  try {
    const extra = { action };
    if (Number.isFinite(positionSeconds)) extra.position_seconds = positionSeconds;
    const response = await api("/api/media/control", authenticatedPayload(extra));
    renderMedia(response.media);
  } catch (error) {
    elements.mediaMessage.textContent = `Room control failed: ${error.message}`;
    event(`Media control failed: ${error.message}`);
  }
}

async function enableLocalAudio() {
  runtime.audioEnabled = true;
  elements.mediaMessage.textContent = "This device speaker is enabled. Select the Bluetooth output in Windows Sound settings.";
  if (runtime.mediaState?.status === "PLAYING") {
    try {
      await elements.roomAudio.play();
    } catch {
      runtime.audioEnabled = false;
      elements.mediaMessage.textContent = "The browser still blocked playback. Select Play room once on this device.";
    }
  }
  event("Enabled media playback on this device");
}

function numericPosition(prefix = "live") {
  const inputs = prefix === "join"
    ? [elements.positionU, elements.positionV, elements.positionW]
    : [elements.liveU, elements.liveV, elements.liveW];
  const values = inputs.map((input) => Number(input.value));
  if (!values.every(Number.isFinite)) {
    throw new Error("U, V, and W must be finite numbers");
  }
  return { u: values[0], v: values[1], w: values[2] };
}

function copyJoinPositionToLive() {
  elements.liveU.value = elements.positionU.value;
  elements.liveV.value = elements.positionV.value;
  elements.liveW.value = elements.positionW.value;
  saveLivePosition();
}

function saveLivePosition() {
  try {
    localStorage.setItem("blueshare.position", JSON.stringify(numericPosition("live")));
  } catch {
    // Invalid in-progress input is reported when the next heartbeat is sent.
  }
}

function nextPositionSeq() {
  runtime.positionSeq += 1;
  sessionStorage.setItem("blueshare.positionSeq", String(runtime.positionSeq));
  return runtime.positionSeq;
}

function saveSession(session) {
  runtime.session = session;
  sessionStorage.setItem("blueshare.session", JSON.stringify(session));
}

function clearSession() {
  runtime.session = null;
  sessionStorage.removeItem("blueshare.session");
  if (runtime.timer) {
    clearInterval(runtime.timer);
    runtime.timer = null;
  }
  if (runtime.mediaTimer) {
    clearInterval(runtime.mediaTimer);
    runtime.mediaTimer = null;
  }
  elements.roomAudio.pause();
}

function setMMUKOState(state) {
  elements.mmukoState.textContent = state;
  elements.mmukoState.dataset.state = state;
}

function positionText(position) {
  return `(${position.u.toFixed(2)}, ${position.v.toFixed(2)}, ${position.w.toFixed(2)})`;
}

function peerCard(peer) {
  const article = document.createElement("article");
  article.className = `peer${peer.is_self ? " self" : ""}`;

  const head = document.createElement("div");
  head.className = "peer-head";
  const name = document.createElement("h3");
  name.textContent = peer.is_self ? `${peer.name} · this device` : peer.name;
  const state = document.createElement("span");
  state.className = `peer-state${peer.state === "REMEMBER" ? " remember" : ""}`;
  state.textContent = peer.state;
  head.append(name, state);

  const details = document.createElement("dl");
  const entries = [
    ["Position", positionText(peer.position)],
    ["Distance", peer.distance_from_requester_m === null ? "—" : `${peer.distance_from_requester_m.toFixed(3)} m`],
    ["Last seen", `${peer.last_seen_age_s.toFixed(1)} s`],
    ["Heartbeats", String(peer.heartbeat_count)],
  ];
  for (const [term, value] of entries) {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = term;
    dd.textContent = value;
    details.append(dt, dd);
  }
  article.append(head, details);
  return article;
}

function renderSnapshot(response) {
  setMMUKOState(response.state || elements.mmukoState.textContent);
  elements.connectedCount.textContent = String(response.connected_peer_count);
  elements.lastHeartbeat.textContent = new Date(response.server_time).toLocaleTimeString();
  elements.topologyNote.textContent = `${response.topology} · ${response.peer_count} retained node(s) · coordinates in ${response.coordinate_units}`;
  elements.peerGrid.replaceChildren(...response.peers.map(peerCard));
}

function showDashboard() {
  elements.joinCard.hidden = true;
  elements.dashboard.hidden = false;
}

function showJoin() {
  elements.joinCard.hidden = false;
  elements.dashboard.hidden = true;
}

async function join(eventObject) {
  eventObject.preventDefault();
  elements.formError.textContent = "";
  elements.joinButton.disabled = true;
  try {
    const name = elements.peerName.value.trim();
    localStorage.setItem("blueshare.peerName", name);
    const response = await api("/api/join", {
      pairing_code: elements.pairingCode.value,
      client_id: runtime.clientId,
      name,
      position: numericPosition("join"),
      position_seq: nextPositionSeq(),
    });
    saveSession({ peerId: response.peer_id, sessionToken: response.session_token });
    runtime.positionSeq = Math.max(runtime.positionSeq, response.next_position_seq - 1);
    sessionStorage.setItem("blueshare.positionSeq", String(runtime.positionSeq));
    copyJoinPositionToLive();
    elements.pairingCode.value = "";
    showDashboard();
    renderSnapshot(response);
    event(response.recovered ? "Session rejoined and recovered" : "Joined BlueShare host");
    startHeartbeat(response.heartbeat_interval_ms);
    startMediaPolling();
  } catch (error) {
    elements.formError.textContent = error.message;
    event(`Join failed: ${error.message}`);
  } finally {
    elements.joinButton.disabled = false;
  }
}

async function heartbeat() {
  if (!runtime.session || runtime.heartbeatInFlight) return;
  runtime.heartbeatInFlight = true;
  elements.heartbeatButton.disabled = true;
  try {
    const response = await api("/api/heartbeat", {
      peer_id: runtime.session.peerId,
      session_token: runtime.session.sessionToken,
      position: numericPosition("live"),
      position_seq: nextPositionSeq(),
    });
    setServiceState("online", "Host connected");
    saveLivePosition();
    renderSnapshot(response);
    if (response.recovered) event("Heartbeat recovered node from REMEMBER");
    if (!response.position_accepted) event(`Coordinate rejected: ${response.position_rejection}`);
  } catch (error) {
    setServiceState("offline", "Heartbeat interrupted");
    event(`Heartbeat failed: ${error.message}`);
    if (error.status === 401) {
      clearSession();
      showJoin();
      elements.formError.textContent = "Session expired. Enter the pairing code to rejoin.";
    }
  } finally {
    runtime.heartbeatInFlight = false;
    elements.heartbeatButton.disabled = false;
  }
}

function startHeartbeat(intervalMs = 2000) {
  if (runtime.timer) clearInterval(runtime.timer);
  runtime.timer = setInterval(heartbeat, intervalMs);
  heartbeat();
}

async function leave() {
  if (!runtime.session) return;
  const session = runtime.session;
  clearSession();
  try {
    await api("/api/leave", {
      peer_id: session.peerId,
      session_token: session.sessionToken,
    });
  } catch (error) {
    event(`Leave acknowledgement failed: ${error.message}`);
  }
  showJoin();
  setMMUKOState("LEFT");
  event("Left BlueShare host");
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const health = await response.json();
    setServiceState("online", `Host online · v${health.service_version}`);
  } catch {
    setServiceState("offline", "Host unavailable");
  }
}

function restoreSession() {
  try {
    const stored = JSON.parse(sessionStorage.getItem("blueshare.session"));
    if (stored?.peerId && stored?.sessionToken) {
      runtime.session = stored;
      copyJoinPositionToLive();
      showDashboard();
      event("Restoring browser session");
      startHeartbeat();
      startMediaPolling();
    }
  } catch {
    clearSession();
  }
}

elements.joinForm.addEventListener("submit", join);
elements.heartbeatButton.addEventListener("click", heartbeat);
elements.leaveButton.addEventListener("click", leave);
elements.mediaUploadButton.addEventListener("click", uploadMedia);
elements.mediaEnableButton.addEventListener("click", enableLocalAudio);
elements.mediaPlayButton.addEventListener("click", async () => {
  runtime.audioEnabled = true;
  await controlMedia("play", elements.roomAudio.currentTime || 0);
});
elements.mediaPauseButton.addEventListener("click", () => controlMedia("pause", elements.roomAudio.currentTime || 0));
elements.mediaStopButton.addEventListener("click", () => controlMedia("stop"));
elements.mediaSeek.addEventListener("change", () => {
  const duration = effectiveMediaDuration();
  if (duration <= 0) return;
  const position = (Number(elements.mediaSeek.value) / 1000) * duration;
  synchronizeAudioPosition(position);
  controlMedia("seek", position);
});
elements.localVolume.addEventListener("input", () => {
  const volume = Number(elements.localVolume.value);
  elements.roomAudio.volume = volume;
  localStorage.setItem("blueshare.localVolume", String(volume));
});
elements.roomAudio.addEventListener("loadedmetadata", () => {
  synchronizeAudioPosition(runtime.mediaState?.position_seconds || 0);
  updateMediaTimeline(runtime.mediaState?.position_seconds || 0);
});
elements.roomAudio.addEventListener("timeupdate", () => updateMediaTimeline());
elements.roomAudio.addEventListener("error", () => {
  if (runtime.mediaId) elements.mediaMessage.textContent = "This browser could not decode or load the shared audio file.";
});
elements.clearEvents.addEventListener("click", () => elements.eventList.replaceChildren());
for (const input of [elements.liveU, elements.liveV, elements.liveW]) {
  input.addEventListener("change", saveLivePosition);
}

checkHealth();
restoreSession();
setInterval(checkHealth, 5000);
