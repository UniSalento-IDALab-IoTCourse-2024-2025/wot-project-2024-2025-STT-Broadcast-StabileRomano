# 🎧 Presentazione del progetto

Il progetto si propone di sviluppare un **sistema intelligente per la protezione uditiva e la comunicazione in ambienti di lavoro rumorosi**, utilizzando un'infrastruttura IoT composta da **Raspberry Pi**, **cuffie Bluetooth** e **beacon BLE**.

L'obiettivo è monitorare il livello di pressione sonora dell’ambiente e attivare un filtro elettronico in caso di superamento di una soglia configurabile. Durante questa fase di insonorizzazione, se l’operatore parla, la voce viene convertita in testo tramite un sistema di **Speech-To-Text** e trasmessa agli altri operatori nelle vicinanze. La comunicazione viene poi riprodotta vocalmente tramite **Text-To-Speech**, garantendo una comunicazione efficace senza compromettere la sicurezza.

Il sistema riduce il carico cognitivo e fisico associato all'uso di chat o comandi vocali diretti, mantenendo la comunicazione fluida e discreta. A differenza delle soluzioni esistenti, questo approccio passivo permette di continuare a interagire con i colleghi senza dover rimuovere le cuffie o interrompere le operazioni.

---

# 🔧 Tecnologie e prototipazione

Il sistema sfrutta dispositivi commerciali già disponibili, come **cuffie Bluetooth a basso costo**, e l'attenuazione del rumore viene attualmente **simulata** per la validazione della logica progettuale. L’architettura software è comunque pensata per essere integrabile in un prodotto reale.

Il progetto si inserisce pienamente nell’ambito **IoT**, grazie all’uso di:
- Dispositivi connessi e wearable
- Sensori acustici e beacon BLE
- Elaborazione dei dati in tempo reale
- Tecnologie di comunicazione vocale automatica

Si ispira inoltre ai principi della **Safety Technology**, migliorando la sicurezza sul lavoro in ambienti industriali critici e rumorosi, e della **Wearable Technology**, favorendo un’interazione continua e naturale con il sistema.

---

# 🏗️ Architettura
L'architettura del sistema è raffigurata nel diagramma seguente:

![Architettura del sistema](./assets/images/Design_Architetturale.png)

---

# 📦 Repository GitHub

Il progetto è suddiviso in più componenti, ciascuno con il proprio repository:

- **Mobile-App** – Applicazione Mobile → [GitHub Repo](https://github.com/UniSalento-IDALab-IoTCourse-2024-2025/wot-project-2024-2025-MobileApp-StabileRomano.git)
- **TTS-Receiver** – Ricezione e sintesi vocale del testo in arrivo → [GitHub Repo](https://github.com/UniSalento-IDALab-IoTCourse-2024-2025/wot-project-2024-2025-TTS-Receiver-StabileRomano.git)
  
Inoltre è possibile accedere alla presentazione del progetto al seguente [link](https://unisalento-idalab-iotcourse-2024-2025.github.io/wot-project-presentation-StabileRomano/)

---

# 🎙️ Descrizione  

Questo repository contiene lo **script principale** che gestisce il cuore del sistema di protezione uditiva, implementando le seguenti funzionalità critiche:  

- **Server di comunicazione**  
  - Crea un server dedicato su Raspberry Pi a cui l'app mobile si collega per lo scambio di dati in tempo reale  
  - Gestisce le richieste degli operatori (soglia rumore, stato filtro, etc.) tramite un protocollo leggero ed efficiente  

- **Monitoraggio acustico intelligente**  
  - Analizza costantemente il **livello di pressione sonora** ambientale tramite microfoni collegati  
  - Attiva automaticamente il filtro di insonorizzazione quando viene superata la soglia configurata  

- **Elaborazione vocale avanzata**  
  - In caso di attivazione del filtro, avvia immediatamente il processo di **Speech-To-Text** quando rileva la voce dell'operatore  
  - Trasforma il parlato in testo con bassa latenza e lo trasmette ai colleghi  

- **Coordinamento sistema**  
  - Comunica con i beacon BLE per la geolocalizzazione degli operatori  (tramite il file beacon_status.log aggiornato dal receiver)
  - Invia notifiche all'app mobile sugli eventi critici (attivazione filtro, errori, etc.) 
