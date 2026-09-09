# Corretor de Simulado - Build Automático (GitHub Actions)

Este workflow gera o APK automaticamente na nuvem quando você faz push para o GitHub.

## Como usar

### 1. Criar repositório no GitHub
1. Acesse https://github.com/new
2. Nome: `corretor-simulado`
3. Público ou Privado
4. **Não** inicialize com README (já temos arquivos)

### 2. Subir o código
```cmd
cd C:\Users\Mateus\Documents\corretor_simulado

git init
git add .
git commit -m "Corretor de Simulado - v1.0"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/corretor-simulado.git
git push -u origin main
```
*(Substitua `SEU_USUARIO` pelo seu usuário do GitHub)*

### 3. Build automático
- O build **inicia sozinho** no push
- Acompanhe em: `https://github.com/SEU_USUARIO/corretor-simulado/actions`
- Clique no workflow "Build APK" → veja o log ao vivo

### 4. Baixar o APK
- Quando terminar (✅ verde), clique no workflow
- Na seção **Artifacts** → `corretor-simulado-apk`
- Baixe o ZIP → extraia → instale no celular

### 5. Build manual (sem push)
- Aba **Actions** → **Build APK** → **Run workflow** → **Run workflow**

---

## Tempo de build
- **Primeira vez**: 15-25 min (baixa NDK, SDK, compila Python)
- **Próximas vezes**: 3-5 min (cache do GitHub Actions)

---

## Requisitos no `buildozer.spec` já configurados:
- ✅ Python 3.11
- ✅ Kivy + OpenCV + NumPy
- ✅ Permissão CAMERA
- ✅ Android API 31 (min 21)
- ✅ Arquiteturas: arm64-v8a + armeabi-v7a
- ✅ Orientação portrait
- ✅ AndroidX habilitado

---

## Se der erro no build:
1. Aba **Actions** → clique no workflow falho
2. Baixe artifact `build-logs` 
3. Veja `.buildozer/android/platform/build-*/logs/`
4. Erros comuns:
   - **Memória**: buildozer usa ~4GB, GitHub dá 7GB (ok)
   - **Licenças SDK**: `android.sdk_path` aceita licenças auto
   - **Dependência faltando**: adicione em `requirements =`

---

## Próximo passo após calibrar:
1. Ajuste `detector.py` com coordenadas calibradas
2. `git add . && git commit -m "Calibração finalizada" && git push`
3. APK pronto para instalar no celular!