---
title: Budowanie SIEM w Proxmox - Część I
date: 2025-07-08
tags:
  - blueteam
  - siem
  - homelab
draft: false
---
Security Information and Event Management - system do centralnego gromadzenia, zarządzania, analizowania i korelacji logów oraz incydentów bezpieczeństwa. To dzięki niemu SOC jest w stanie odpowiednio szybko i precyzyjnie zareagować na zagrożenia w infrastrukturze IT. A myśleliście, żeby postawić takie coś u siebie - korzystając jedynie z darmowych i open-sourcowych narzędzi? W tej mini serii pokażę Wam jak w prosty sposób stworzyć własny wirtualny SIEM sandbox w Proxmox bazujący na Security Onion. Od zera.

## Sprzęt

Gdy pierwszy raz wybierałem hardware, nie miałem jeszcze konkretnego planu stworzenia wirtualnego labu do nauki cyber. Wiedziałem jednak, że będę mocno eksperymentował z szeroko pojętą wirtualizacją i konteneryzacją. Potrzebowałem coś co starczy na dłużej. Zależało mi głównie na:
- modularności - możliwości dołożenia dodatkowego RAM-u, zmiany CPU
- niskiej cenie
- małym rozmiarze
- niskim poborze prądu

Szybko zorientowałem się, że Raspberry nie jest tu dobrym rozwiązaniem. Wysoka cena oraz brak możliwości zmiany CPU czy RAM skutecznie mnie zniechęciły. Stąd moje oczy zwróciły się ku terminalom/mini-PC. Modularność, niższa cena i prostota wymiany komponentów to było coś czego szukałem. Wybór konkretnego modelu nie należał jednak do prostych, ale z pomocą przyszedł mi świetny film kanału tata.geek (Pozdrawiam!), gdzie porównuje najpopularniejsze i tanie terminale do wirtualizacji/self-hostingu. Chyba każdy z wymienionych modeli można znaleźć na Allegro.

{{< youtubeLite id="SgXhGb-7QbU" label="Blowfish-tools demo" >}}

Ja ostatecznie zdecydowałem się na model **HP EliteDesk 800 G3**. Co na pokładzie?
- Intel Core i3-6100T
- 32 GB RAM-u DDR4 2666MHz (SODIMM). Początkowo miał tylko 8, więc dokupiłem. Dostępne są 2 sloty
- Dysk SSD m.2 SATA 256 GB. Później dokupiłem kolejny - tym razem SSD 256 GB na SATA, co patrząc z dzisiejszej perspektywy było słabym wyborem i mogłem dać większą pojemność. 

Wymiana podzespołów jest tak łatwa jak budowanie z klocków Lego. Nawet osoba nie składająca wcześniej PC nie będzie miała problemu z podstawowymi naprawami i konserwacją.

Udostępniam też film pokazujący więcej szczegółów terminala.


No dobra, ale co z ceną? Mi swojego (używanego) udało się kupić za 268 zł na Allegro. Także  całkiem w porządku. Oczywiście są tańsze modele - warto jednak sprawdzić na ile możemy sobie pozwolić zmianę podzespołów. Może się zdarzyć, że maksymalnie możemy mieć np. 16 GB.

## Hypervisor

Kiedy już wybraliśmy mini-PC, musimy wybrać hypervisora, czyli menedżera odpowiedzialnego za zarządzanie maszynami wirtualnymi/kontenerami i przydzielanie im fizycznych zasobów. Wyróżniamy 2 typy:
- Typ I
- Typ II

Typ I tzw. bare-metal charakteryzuje się tym, że działa bezpośrednio na sprzęcie fizycznym. Dzięki temu