clear();

console.log('=== TLA K.O. DETECTION + Raspberry Pi SIGNAL ===');

// ======= CONFIG (EDIT THESE) =======
const PI_HOST  = "http://172.26.53.118:8000"; // <-- your Pi IP + port
const PI_TOKEN = "change-me";                 // <-- must match SECRET in ko_server.py
// ===================================

// Fire-and-forget LAN signal (works well even when fetch/CORS is annoying)
function notifyPi(koType, timerVal) {
  const url =
    `${PI_HOST}/ko?token=${encodeURIComponent(PI_TOKEN)}` +
    `&type=${encodeURIComponent(koType)}` +
    `&timer=${encodeURIComponent(timerVal)}` +
    `&t=${Date.now()}`; // cache-buster

  // Send request
  const img = new Image();

  // Helpful browser-side feedback
  img.onload  = () => console.log(`📡 Sent to Pi: ${koType} @ ${timerVal}s`);
  img.onerror = () => console.log(`⚠️ Could not reach Pi (blocked/unreachable): ${url}`);

  img.src = url;
}

// Quick manual test you can run anytime:
// notifyPi("test", 99);

let timer = 0;
let lastTimer = -1;
let timerFreezeCount = 0;
let lastKOTime = 0;
let koTriggeredThisFreeze = false;

const FREEZE_THRESHOLD = 30;    // 30 * 100ms = 3s of freeze
const COOLDOWN_MS = 8000;       // 8s cooldown between KOs

// Hook canvas fillText to capture the HUD timer
(function hookTimer() {
  const origFillText = CanvasRenderingContext2D.prototype.fillText;

  CanvasRenderingContext2D.prototype.fillText = function (text, x, y) {
    const str = String(text);

    // Heuristic: timer is usually 1–2 digits, top region of screen, middle-ish X.
    if (/^\d{1,2}$/.test(str) && y < 150 && x > 200 && x < 800) {
      const val = parseInt(str, 10);
      if (!Number.isNaN(val)) {
        timer = val;
        window.currentTimer = timer; // for debugging
      }
    }

    return origFillText.apply(this, arguments);
  };

  console.log('✓ Canvas timer hook installed');
})();

// Monitor freezes
setInterval(() => {
  if (timer === lastTimer && timer >= 0) {
    timerFreezeCount++;

    if (timerFreezeCount % 10 === 0) {
      console.log(
        `⏸️  Frozen: ${timerFreezeCount} ticks ` +
        `(${(timerFreezeCount * 0.1).toFixed(1)}s) at timer=${timer}`
      );
    }

    if (timerFreezeCount === FREEZE_THRESHOLD && !koTriggeredThisFreeze) {
      const now = Date.now();

      if (timer > 85) {
        console.log('⏭️  Timer > 85 - likely intro, skipping');
      } else if (timer >= 3 && now - lastKOTime > COOLDOWN_MS) {
        // Regular health K.O.
        console.log('💀 K.O. DETECTED (health)!');
        console.log(`   Timer: ${timer}s`);

        notifyPi("health", timer);   // <-- SEND TO PI

        lastKOTime = now;
        koTriggeredThisFreeze = true;
      } else if (timer === 0 && now - lastKOTime > COOLDOWN_MS) {
        // Time-out K.O. at 00
        console.log('⌛ K.O. DETECTED (time up)!');
        console.log('   Timer: 0s (TIME UP)');

        notifyPi("timeup", 0);       // <-- SEND TO PI

        lastKOTime = now;
        koTriggeredThisFreeze = true;
      } else {
        console.log(
          `⏭️  Cooldown active (${((now - lastKOTime) / 1000).toFixed(1)}s < ${(COOLDOWN_MS / 1000).toFixed(0)}s)`
        );
      }
    }
  } else {
    if (timerFreezeCount >= 5) {
      console.log(`✓ Freeze ended after ${timerFreezeCount} ticks`);
    }
    timerFreezeCount = 0;
    koTriggeredThisFreeze = false;
  }

  lastTimer = timer;
}, 100);

// Detect match end via DOM text changes
new MutationObserver(() => {
  const text = document.body.innerText;
  if (text.includes('REMATCH') || text.includes('wins!')) {
    const now = Date.now();
    if (now - lastKOTime > 3000) {
      console.log('🏁 Match ended!');
      lastKOTime = now;
    }
  }
}).observe(document.body, { childList: true, subtree: true });

console.log('✓ K.O. detection active');
console.log('📊 8-second cooldown to skip "Ready..." after K.O.');
console.log('🧪 To test right now, run: notifyPi("test", 99)');
