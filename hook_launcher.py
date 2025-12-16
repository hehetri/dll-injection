import frida
import sys
import time

PROCESS_NAME = "t-bot.dat.exe.exe"

JS_CODE = r"""
'use strict';

// =======================
// ENDEREÇOS IMPORTANTES
// =======================
const GAME_STATE      = ptr("0x007930e0"); // estado principal
const GAME_SUBSTATE   = ptr("0x007930e4"); // subestado
const CHAR_INDEX      = ptr("0x0078cd20"); // personagem atual (0,1,2)

// =======================
// WINAPI
// =======================
const user32 = Module.load("user32.dll");
const GetAsyncKeyState = new NativeFunction(
    Module.getExportByName("user32.dll", "GetAsyncKeyState"),
    "int",
    ["int"]
);

// VK CODES
const VK_F2     = 0x71;
const VK_LEFT   = 0x25;
const VK_RIGHT  = 0x27;
const VK_RETURN = 0x0D;

// =======================
// BASE / LOOP
// =======================
const base = Module.findBaseAddress("t-bot.dat.exe.exe");
console.log("[OK] Base:", base);

// Loop principal
const TICK = base.add(0x3A92A0); // FUN_004a92a0

let lastState = -1;
let keyLock = false;

Interceptor.attach(TICK, {
    onEnter() {

        // =======================
        // DUMP DE ESTADOS
        // =======================
        const state = Memory.readU32(GAME_STATE);
        if (state !== lastState) {
            console.log("[STATE]", lastState, "->", state);
            lastState = state;
        }

        // =======================
        // HOTKEY F2
        // =======================
        if (GetAsyncKeyState(VK_F2) & 1) {
            console.log("[HOTKEY] F2 → Seleção de personagem");
            Memory.writeU32(GAME_STATE, 3);
            Memory.writeU32(GAME_SUBSTATE, 0);
        }

        // =======================
        // SELEÇÃO (somente no estado 3)
        // =======================
        if (state === 3) {

            let idx = Memory.readU16(CHAR_INDEX);

            if (GetAsyncKeyState(VK_LEFT) & 1) {
                idx = (idx + 2) % 3;
                Memory.writeU16(CHAR_INDEX, idx);
                console.log("[CHAR] ←", idx);
            }

            if (GetAsyncKeyState(VK_RIGHT) & 1) {
                idx = (idx + 1) % 3;
                Memory.writeU16(CHAR_INDEX, idx);
                console.log("[CHAR] →", idx);
            }

            if (GetAsyncKeyState(VK_RETURN) & 1) {
                console.log("[CHAR] Confirmado:", idx);
                // cliente segue fluxo normal
            }
        }
    }
});
"""

def on_message(message, data):
    print("[FRIDA]", message)

def main():
    device = frida.get_local_device()

    pid = None
    for p in device.enumerate_processes():
        if p.name.lower() == PROCESS_NAME.lower():
            pid = p.pid
            break

    if pid is None:
        print("[-] Processo não encontrado")
        sys.exit(1)

    print("[+] Conectando ao processo PID:", pid)
    session = device.attach(pid)

    script = session.create_script(JS_CODE)
    script.on("message", on_message)
    script.load()

    print("[+] Hook ativo")
    print("F2 = abrir seleção")
    print("← → = trocar personagem")
    print("ENTER = confirmar")
    print("CTRL+C para sair")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        session.detach()

if __name__ == "__main__":
    main()
