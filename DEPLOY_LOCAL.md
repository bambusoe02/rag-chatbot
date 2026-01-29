# 🚀 Lokalne Wdrożenie - Przewodnik Krok po Kroku

## 📋 Co Musisz Wiedzieć Przed Startem

### ✅ Wymagania Systemowe

**Minimum:**
- **RAM:** 8GB (16GB zalecane)
- **Dysk:** 20GB wolnego miejsca
- **CPU:** 4 rdzenie
- **OS:** Linux, macOS, Windows (z WSL2)

**Oprogramowanie:**
- Docker 20.10+
- Docker Compose 2.0+
- Git

### 🔍 Sprawdzenie Przed Startem

#### 1. Zainstaluj Docker (jeśli nie masz)

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Wyloguj się i zaloguj ponownie
```

**macOS:**
```bash
# Pobierz Docker Desktop z:
# https://www.docker.com/products/docker-desktop
```

**Windows:**
```bash
# Pobierz Docker Desktop z:
# https://www.docker.com/products/docker-desktop
# Włącz WSL2
```

#### 2. Sprawdź Instalację

```bash
docker --version
docker-compose --version
```

#### 3. Sprawdź Porty

```bash
# Sprawdź czy porty są wolne
lsof -i :8000  # Backend
lsof -i :8501  # Frontend

# Jeśli zajęte, zatrzymaj procesy lub zmień porty w docker-compose.yml
```

#### 4. Przygotuj Konfigurację

```bash
# Skopiuj przykładowy .env (jeśli nie istnieje)
cp .env.example .env

# Edytuj .env i ustaw:
# - SECRET_KEY (wygeneruj: openssl rand -hex 32)
# - DATABASE_URL (domyślnie SQLite, OK dla lokalnego)
# - Inne ustawienia według potrzeb
```

---

## 🚀 Szybki Start (5 minut)

### Krok 1: Sklonuj Repozytorium (jeśli jeszcze nie)

```bash
git clone <your-repo-url>
cd rag-chatbot
```

### Krok 2: Skonfiguruj Środowisko

```bash
# Utwórz .env z przykładowych wartości
cp .env.example .env

# Wygeneruj SECRET_KEY
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

### Krok 3: Uruchom Wszystkie Serwisy

```bash
# Uruchom wszystkie kontenery
docker-compose up -d

# Sprawdź status
docker-compose ps
```

### Krok 4: Poczekaj na Start (30-60 sekund)

```bash
# Sprawdź logi
docker-compose logs -f

# Naciśnij Ctrl+C aby wyjść z logów
```

### Krok 5: Sprawdź Czy Działa

```bash
# Health check backend
curl http://localhost:8000/health/status

# Powinno zwrócić: {"status":"healthy"}

# Otwórz w przeglądarce:
# Frontend: http://localhost:8501
# Backend API: http://localhost:8000/docs
```

---

## 📊 Co Jest Uruchomione?

Po `docker-compose up -d` masz:

| Serwis | Port | URL | Opis |
|--------|------|-----|------|
| **Frontend** | 8501 | http://localhost:8501 | Streamlit UI |
| **Backend** | 8000 | http://localhost:8000 | FastAPI API |
| **API Docs** | 8000 | http://localhost:8000/docs | Swagger UI |
| **ReDoc** | 8000 | http://localhost:8000/redoc | ReDoc docs |
| **Redis** | 6379 | - | Cache (wewnętrzny) |
| **PostgreSQL** | 5432 | - | Baza danych (wewnętrzny) |
| **Ollama** | 11434 | - | LLM (wewnętrzny) |

---

## 🔧 Podstawowe Komendy

### Zarządzanie Serwisami

```bash
# Uruchom wszystkie serwisy
docker-compose up -d

# Zatrzymaj wszystkie serwisy
docker-compose down

# Zatrzymaj i usuń dane (UWAGA: usuwa bazy danych!)
docker-compose down -v

# Restart konkretnego serwisu
docker-compose restart backend

# Zobacz logi
docker-compose logs -f
docker-compose logs backend -f  # tylko backend
```

### Sprawdzanie Statusu

```bash
# Lista uruchomionych kontenerów
docker-compose ps

# Status zdrowia
docker-compose ps --format "table {{.Name}}\t{{.Status}}"

# Sprawdź użycie zasobów
docker stats
```

### Debugowanie

```bash
# Wejdź do kontenera
docker-compose exec backend bash
docker-compose exec frontend bash

# Sprawdź logi konkretnego serwisu
docker-compose logs backend --tail=100
docker-compose logs frontend --tail=100

# Sprawdź błędy
docker-compose logs | grep -i error
```

---

## ⚠️ Częste Problemy i Rozwiązania

### Problem 1: Port już zajęty

**Błąd:**
```
Error: bind: address already in use
```

**Rozwiązanie:**
```bash
# Znajdź proces używający portu
lsof -i :8000
lsof -i :8501

# Zatrzymaj proces
kill -9 <PID>

# LUB zmień porty w docker-compose.yml
```

### Problem 2: Brak pamięci

**Błąd:**
```
Cannot allocate memory
```

**Rozwiązanie:**
```bash
# Sprawdź użycie pamięci
docker stats

# Zatrzymaj inne kontenery Docker
docker ps
docker stop <container-id>

# Zwiększ limit pamięci w Docker Desktop (Settings > Resources)
```

### Problem 3: Backend nie startuje

**Rozwiązanie:**
```bash
# Sprawdź logi
docker-compose logs backend

# Sprawdź czy baza danych jest gotowa
docker-compose exec backend python -c "from backend.database import engine; engine.connect()"

# Zrestartuj backend
docker-compose restart backend
```

### Problem 4: Frontend nie ładuje się

**Rozwiązanie:**
```bash
# Sprawdź logi
docker-compose logs frontend

# Sprawdź czy backend działa
curl http://localhost:8000/health/status

# Zrestartuj frontend
docker-compose restart frontend
```

### Problem 5: Błąd z Ollama (model nie znaleziony)

**Rozwiązanie:**
```bash
# Wejdź do kontenera Ollama
docker-compose exec ollama bash

# Pobierz model
ollama pull qwen2.5:14b-instruct

# LUB w docker-compose.yml dodaj init command
```

---

## 🔐 Konfiguracja Bezpieczeństwa (Lokalnie)

Dla lokalnego użycia, podstawowa konfiguracja jest OK. Ale jeśli chcesz:

### Zmień domyślne hasła

```bash
# Edytuj .env
nano .env

# Zmień:
ADMIN_PASSWORD=twoje_bezpieczne_haslo
DATABASE_PASSWORD=twoje_haslo_bazy
```

### Wygeneruj nowy SECRET_KEY

```bash
# Wygeneruj losowy klucz
openssl rand -hex 32

# Dodaj do .env
echo "SECRET_KEY=wygenerowany_klucz" >> .env
```

---

## 📊 Monitorowanie (Opcjonalne)

### Sprawdź Zasoby

```bash
# Użycie CPU i RAM
docker stats

# Użycie dysku
docker system df
```

### Sprawdź Logi

```bash
# Wszystkie logi
docker-compose logs -f

# Tylko błędy
docker-compose logs | grep -i error

# Ostatnie 100 linii
docker-compose logs --tail=100
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health/status

# Backend metrics
curl http://localhost:8000/metrics

# Frontend (sprawdź w przeglądarce)
open http://localhost:8501
```

---

## 🧪 Testowanie Po Instalacji

### 1. Test Backend API

```bash
# Health check
curl http://localhost:8000/health/status

# Powinno zwrócić: {"status":"healthy"}
```

### 2. Test Frontend

```bash
# Otwórz w przeglądarce
open http://localhost:8501

# Powinieneś zobaczyć interfejs logowania
```

### 3. Test Upload Dokumentu

1. Zaloguj się (lub utwórz konto)
2. Przejdź do "Upload Documents"
3. Prześlij testowy PDF
4. Poczekaj na przetworzenie (30-60 sekund)

### 4. Test Pytania

1. Po przesłaniu dokumentu, przejdź do chat
2. Zadaj pytanie o zawartość dokumentu
3. Sprawdź czy otrzymujesz odpowiedź

---

## 🗑️ Czyszczenie (Jeśli Coś Pójdzie Nie Tak)

### Zatrzymaj i Usuń Wszystko

```bash
# Zatrzymaj kontenery
docker-compose down

# Usuń kontenery i wolumeny (UWAGA: usuwa dane!)
docker-compose down -v

# Usuń obrazy (opcjonalnie)
docker-compose down --rmi all

# Wyczyść system Docker (opcjonalnie)
docker system prune -a
```

### Reset Bazy Danych

```bash
# Zatrzymaj serwisy
docker-compose down

# Usuń wolumeny bazy danych
docker volume rm rag-chatbot_postgres_data
docker volume rm rag-chatbot_chromadb_data

# Uruchom ponownie
docker-compose up -d
```

---

## 📝 Następne Kroki

Po udanym lokalnym wdrożeniu:

1. ✅ **Przetestuj wszystkie funkcje**
   - Upload dokumentów
   - Zadawanie pytań
   - API keys
   - Analytics

2. ✅ **Zapoznaj się z dokumentacją**
   - [User Guide](docs/user/README.md)
   - [API Documentation](docs/api/authentication.md)

3. ✅ **Przygotuj się do produkcji**
   - Przejrzyj [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)
   - Uruchom `python optimize.py`
   - Uruchom `python performance_benchmark.py`

4. ✅ **Rozważ wdrożenie w chmurze**
   - [Cloud Deployment Guide](cloud/README.md)
   - [Kubernetes Guide](k8s/README.md)

---

## 🆘 Potrzebujesz Pomocy?

- 📖 Sprawdź [Troubleshooting Guide](docs/user/troubleshooting/common-issues.md)
- 💬 Sprawdź logi: `docker-compose logs`
- 🐛 Zgłoś problem na GitHub Issues

---

**Gotowy do startu? Uruchom:**

```bash
docker-compose up -d
```

**Powodzenia! 🚀**

