# UGREEN LED Manager

Weboberfläche zur Konfiguration der Front-LEDs auf UGREEN DXP NAS-Geräten unter ZimaOS.

## Funktionen

- Power-, Netzwerk- und Disk-LEDs konfigurieren
- Farben **und Helligkeit** anpassen
- Disk-Zustände für **Aktiv**, **Standby** und **Fehler**
- Deutsch / Englisch in der Weboberfläche
- Ressourcenschonender Betrieb mit Flask + Vanilla JS
- ZimaOS Custom App per Docker Compose

## Wichtige Voraussetzung

Diese App **setzt `ugreen_leds_cli` voraus**.

Die App bringt die UGREEN-CLI **nicht selbst** mit.  
Die CLI muss **vorher auf dem ZimaOS-Host** installiert, getestet und an einen dauerhaften Host-Pfad gelegt werden.

Empfohlener Host-Pfad:

```text
/DATA/AppData/ugreen-led/bin/ugreen_leds_cli
