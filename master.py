from SX127x.LoRa import LoRa
from SX127x.board_config import BOARD
from SX127x.constants import MODE, BW, CODING_RATE
import time

time.sleep(0.2)

class LoRaSender(LoRa):
    def __init__(self):
        super(LoRaSender, self).__init__(verbose=False)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])

    def on_tx_done(self):
        self.set_mode(MODE.STDBY)

BOARD.setup()
lora = LoRaSender()

print("LoRa Sender")

lora.set_freq(433.0)
lora.set_pa_config(pa_select=1)
lora.set_bw(BW.BW250)
lora.set_spreading_factor(7)
lora.set_coding_rate(CODING_RATE.CR4_5)
lora.set_preamble(16)
lora.set_sync_word(0x12)

lora.set_mode(MODE.STDBY)

try:
    while True:
        msg = input("Enter up to 6 characters to send: ")
        msg = msg[:6].ljust(6)
        payload = [ord(c) for c in msg]

        lora.write_payload(payload)
        lora.clear_irq_flags(TxDone=1, RxDone=1, PayloadCrcError=1)

        lora.set_mode(MODE.TX)
        print(f"Sent: '{msg}' Waiting for TX to complete…")

        while True:
            irq_flags = lora.get_irq_flags()
            if irq_flags.get('tx_done'):
                lora.clear_irq_flags(TxDone=1)
                print("TX complete.")
                break
            time.sleep(0.01)

        lora.set_mode(MODE.RXCONT)
        print("Listening for ACK…")

        ack_received = False
        start_time = time.time()
        while time.time() - start_time < 1.5:  # wait 1.5 seconds for ACK
            irq_flags = lora.get_irq_flags()
            if irq_flags.get('rx_done'):
                lora.clear_irq_flags(RxDone=1, PayloadCrcError=1)
                payload = lora.read_payload(nocheck=True)
                ack = ''.join([chr(c) for c in payload[:6]]).strip()
                print(f"ACK received: '{ack}'")
                ack_received = True
                break
            time.sleep(0.01)

        if not ack_received:
            print("No ACK received.")

        lora.set_mode(MODE.STDBY)
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Closing…")

finally:
    BOARD.teardown()
