import frida
import sys
import time

PROCESS_NAME = "t-bot.dat.exe.exe"

JS_CODE = r"""
'use strict';

const PROCESS = "t-bot.dat.exe.exe";

// Endereços globais (do seu dump)
const GAME_STATE    = ptr("0x007930e0"); // DAT_007930e0
const GAME_SUBSTATE = ptr("0x007930e4"); // DAT_007930e4

console.log("[*] Hook JS carregado");

const moduleInfo = Process.enumerateModulesSync().find(m => m.name.toLowerCase() === PROCESS.toLowerCase());
if (!moduleInfo) {
    console.log("[ERRO] Base do módulo não encontrada");
} else {
    const base = moduleInfo.base;
    console.log("[OK] Base:", base);

    // Função de tick (chamada constantemente)
    const TICK_FUNC = base.add(0x3A92A0); // FUN_004a92a0

    Interceptor.attach(TICK_FUNC, {
        onEnter(args) {
            const state = Memory.readU32(GAME_STATE);

            // 3 = seleção de personagem
            if (state !== 3) {
                console.log("[HOOK] Forçando tela de seleção");
                Memory.writeU32(GAME_STATE, 3);
                Memory.writeU32(GAME_SUBSTATE, 0);
            }
        }
    });
}
"""

def on_message(message, data):
    print("[FRIDA]", message)

def main():
    device = frida.get_local_device()
    pid = None

    for proc in device.enumerate_processes():
        if proc.name.lower() == PROCESS_NAME.lower():
            pid = proc.pid
            break

    if pid is None:
        print("[-] Processo não encontrado:", PROCESS_NAME)
        sys.exit(1)

    print(f"[+] Conectando ao processo PID: {pid}")
    session = device.attach(pid)

    script = session.create_script(JS_CODE)
    script.on("message", on_message)
    script.load()

    print("[+] Hook ativo! Tela de seleção será forçada automaticamente.")
    print("[*] Pressione CTRL+C para sair.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Encerrando hook...")
        session.detach()

if __name__ == "__main__":
    main()
