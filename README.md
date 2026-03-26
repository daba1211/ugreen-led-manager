# UGREEN LED Manager (DXP4800 Pro)

## Deutsch

### Beschreibung

Mit diesem Projekt kann man die Front-LEDs eines UGREEN DXP NAS unter ZimaOS über eine einfache Weboberfläche steuern.

### Voraussetzung

Bevor diese App installiert wird, muss die CLI `ugreen_leds_cli` bereits auf dem ZimaOS-Host vorhanden sein.

Die CLI stammt aus diesem Projekt:

- https://github.com/miskcoo/ugreen_leds_controller

Das Upstream-Projekt beschreibt, dass die LED-Steuerung über I2C erfolgt, `i2c-dev` benötigt wird und dass sich Kommandozeilen-Tool und Kernel-Modul `led_ugreen` gegenseitig in die Quere kommen. Für die Nutzung der CLI soll `led_ugreen` daher entladen sein.

### CLI vorbereiten

#### `i2c-dev` laden

```bash
modprobe -v i2c-dev
```

#### Prüfen, ob `led_ugreen` geladen ist

```bash
lsmod | grep led_ugreen
```

Falls das Modul geladen ist, sollte es für die Nutzung der CLI entladen werden:

```bash
modprobe -r led_ugreen
```

#### CLI an einen dauerhaften Pfad legen

```bash
mkdir -p /DATA/AppData/ugreen-led/bin
cp /PFAD/ZUR/ugreen_leds_cli /DATA/AppData/ugreen-led/bin/ugreen_leds_cli
chmod 755 /DATA/AppData/ugreen-led/bin/ugreen_leds_cli
```

#### CLI kurz testen

```bash
/DATA/AppData/ugreen-led/bin/ugreen_leds_cli power -status
/DATA/AppData/ugreen-led/bin/ugreen_leds_cli power -on -color 0 0 255 -brightness 255
/DATA/AppData/ugreen-led/bin/ugreen_leds_cli all -off
```

Die Upstream-CLI unterstützt unter anderem `-color`, `-brightness`, `-on`, `-off` und LEDs wie `power`, `netdev`, `disk1` bis `disk8`.

### App über Docker Compose installieren

Nachdem die CLI funktioniert, kann diese App installiert werden.

#### Repository klonen

```bash
git clone https://github.com/daba1211/ugreen-led-manager.git
cd ugreen-led-manager
```

#### Compose-Datei verwenden

In diesem Repository liegt die Datei:

```text
docker-compose.zimaos.yml
```

Diese Datei kann direkt in ZimaOS als Custom App verwendet werden.

#### In ZimaOS importieren

1. ZimaOS öffnen
2. oben rechts auf **+** klicken
3. **Install a customized app** auswählen
4. **Import** öffnen
5. den Reiter **Docker Compose** wählen
6. den Inhalt von `docker-compose.zimaos.yml` aus diesem Repository einfügen
7. speichern / deployen

### Hinweis

Die Entwicklung dieses Projekts wurde mit Hilfe von ChatGPT unterstützt.  
Die eigentliche LED-Ansteuerung basiert auf der CLI aus dem Projekt `miskcoo/ugreen_leds_controller`.

### Dank

Vielen Dank an den Ersteller von `ugreen_leds_controller`.  
Ohne dieses Projekt und die bereitgestellte CLI wäre diese App in dieser Form nicht möglich gewesen.

---

## English

### Description

This project allows me to control the front LEDs of my UGREEN DXP NAS on ZimaOS through a simple web interface.

### Requirement

Before installing this app, the `ugreen_leds_cli` CLI must already be available on the ZimaOS host.

The CLI comes from this project:

- https://github.com/miskcoo/ugreen_leds_controller

The upstream project explains that LED control is done over I2C, requires `i2c-dev`, and that the command-line tool conflicts with the `led_ugreen` kernel module. To use the CLI, `led_ugreen` should therefore be unloaded.

### Prepare the CLI

#### Load `i2c-dev`

```bash
modprobe -v i2c-dev
```

#### Check whether `led_ugreen` is loaded

```bash
lsmod | grep led_ugreen
```

If the module is loaded, it should be unloaded before using the CLI:

```bash
modprobe -r led_ugreen
```

#### Place the CLI in a permanent path

```bash
mkdir -p /DATA/AppData/ugreen-led/bin
cp /PATH/TO/ugreen_leds_cli /DATA/AppData/ugreen-led/bin/ugreen_leds_cli
chmod 755 /DATA/AppData/ugreen-led/bin/ugreen_leds_cli
```

#### Quick CLI test

```bash
/DATA/AppData/ugreen-led/bin/ugreen_leds_cli power -status
/DATA/AppData/ugreen-led/bin/ugreen_leds_cli power -on -color 0 0 255 -brightness 255
/DATA/AppData/ugreen-led/bin/ugreen_leds_cli all -off
```

The upstream CLI supports options such as `-color`, `-brightness`, `-on`, `-off`, and LEDs like `power`, `netdev`, and `disk1` to `disk8`.

### Install the app via Docker Compose

Once the CLI is working, this app can be installed.

#### Clone the repository

```bash
git clone https://github.com/daba1211/ugreen-led-manager.git
cd ugreen-led-manager
```

#### Use the Compose file

This repository contains the file:

```text
docker-compose.zimaos.yml
```

This file can be used directly in ZimaOS as a custom app.

#### Import it into ZimaOS

1. Open ZimaOS
2. click **+** in the top right corner
3. choose **Install a customized app**
4. open **Import**
5. select the **Docker Compose** tab
6. paste the contents of `docker-compose.zimaos.yml` from this repository
7. save / deploy

### Note

The development of this project was supported with the help of ChatGPT.  
The actual LED control is based on the CLI from the `miskcoo/ugreen_leds_controller` project.

### Thanks

Many thanks to the creator of `ugreen_leds_controller`.  
Without that project and the provided CLI, this app would not have been possible in this form.
