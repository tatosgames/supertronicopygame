# Boot Tuning

Use these commands when boot feels slow or Plymouth hangs too long.

## Boot Check

```bash
cd ~/supertronicopygame
bash scripts/boot-check.sh
```

Full report:

```bash
cd ~/supertronicopygame
bash scripts/boot-check.sh --full
```

The report focuses on:

- boot timing
- top boot delays
- Plymouth
- NetworkManager wait-online
- display/session startup
- TFT/driver lines

## Boot Speedup

```bash
cd ~/supertronicopygame
sudo bash scripts/boot-speedup.sh
```

It will:

- back up `cmdline.txt`
- remove `quiet splash`
- disable and mask `NetworkManager-wait-online.service`
- mask Plymouth services if they exist

After it finishes, reboot:

```bash
sudo reboot
```
