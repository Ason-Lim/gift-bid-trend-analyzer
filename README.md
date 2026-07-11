# GitHub 연동 및 Render PostgreSQL 분리 배포 가이드북

선물 트렌드 분석 시스템의 격리 구축을 완료하고, 동일한 Postgres 데이터베이스 서버를 활용하되 데이터베이스 공간을 안전하게 분리하여 Render에 독립 배포하는 전체 매뉴얼입니다.

---

## 1. 독립 프로젝트 구조 구축 완료

신규 독립 폴더 `/Users/mom/gift_trend_analyzer`가 생성되었으며, 프론트엔드/백엔드 코드를 이식하여 독자적인 Git 레포지토리로 초기화를 마쳤습니다.

### [프로젝트 주요 구조]
- **`app.py`**: 단독 구동 포트 설정 및 일반화된 템플릿 경로 연동
- **`database.py`**: PostgreSQL 자동 테이블 매핑 지원
- **`migrate_db.py`**: 로컬 SQLite의 데이터를 PostgreSQL로 전송하는 원클릭 시딩 스크립트
- **`render.yaml`**: Render Blueprint 자동 배포 설정 구성 완료
- **`templates/` & `static/`**: trend 접두사를 걷어내고 독립 패키징 완료

---

## 2. Render PostgreSQL 데이터베이스 분리 (CREATE DATABASE)

하나의 PostgreSQL Basic 모델 요금을 유지하면서, 두 서비스를 완전히 분리된 데이터베이스(Database) 공간에 두도록 설정합니다.

1. **DBeaver, pgAdmin 또는 psql** 등의 데이터베이스 툴을 사용하여 현재 Render PostgreSQL DB 서버에 접속합니다.
   - 호스트 정보 및 접속 계정은 Render PostgreSQL 대시보드의 **'External Connection String'**을 참고하십시오.
2. 접속 후 SQL 편집기를 열어 아래 쿼리를 실행하여 새 독립 DB를 생성합니다.
   ```sql
   CREATE DATABASE gift_trend_db;
   ```
3. 이제 기존 서비스는 기존 DB명(예: `smallbiz_db`)을 바라보고, 신규 서비스는 `gift_trend_db`를 바라보게 되어 데이터 오염을 예방할 수 있습니다.

---

## 3. GitHub 리포지토리 연동 및 소스 업로드

로컬에 생성된 Git 저장소에 GitHub 원격 주소(Remote)를 연결하고 업로드하는 과정입니다.

1. **GitHub 웹사이트**에 접속하여 새 비공개(Private) 또는 공개(Public) 리포지토리를 생성합니다. (예: `gift-bid-trend-analyzer`)
2. 터미널을 열고 `/Users/mom/gift_trend_analyzer` 경로에서 다음 명령어들을 순차적으로 실행하여 GitHub로 푸시합니다.
   ```bash
   cd /Users/mom/gift_trend_analyzer
   git branch -m main
   git remote add origin <GitHub 리포지토리 URL>
   git push -u origin main
   ```

---

## 4. 로컬 SQLite 데이터 ➔ PostgreSQL 원격 마이그레이션

로컬에서 수집한 15건의 소중한 명절/기념일 선물 입찰 데이터(`gift_bids` 테이블)를 신규 생성한 Render Postgres `gift_trend_db`로 즉시 마이그레이션(시딩)합니다.

1. 터미널에서 `DATABASE_URL` 환경 변수와 함께 마이그레이션 스크립트를 실행합니다.
   - `<Render_Postgres_접속_URL>`은 새로 만든 데이터베이스 `gift_trend_db`를 타겟팅하는 주소여야 합니다.
   - 예: `postgresql://user:password@host-red.render.com/gift_trend_db?sslmode=require`
2. **명령어**:
   ```bash
   DATABASE_URL="<Render_Postgres_접속_URL>" python3 migrate_db.py
   ```
3. 실행이 완료되면 PostgreSQL DB 테이블에 15건의 데이터가 멱등성(중복 패스)을 지키며 이식됩니다.

---

## 5. Render 서비스 Blueprint 원클릭 배포

`render.yaml` Blueprint 파일을 적용하여 Render 대시보드에서 몇 번의 클릭만으로 손쉽게 배포할 수 있습니다.

1. **Render 대시보드**에 로그인한 뒤 우측 상단의 **`New +`** ➔ **`Blueprint`**를 선택합니다.
2. 위 3단계에서 푸시한 GitHub 리포지토리를 연동 및 선택합니다.
3. 배포 설정 중 **`DATABASE_URL`** 환경 변수를 입력하는 란이 나타납니다.
   - 여기에 **2단계에서 분리한 PostgreSQL 데이터베이스 연결 URL**을 입력합니다:
     `postgresql://user:password@host-red.render.com/gift_trend_db?sslmode=require`
4. **`Apply`** 버튼을 누르면 Render가 `render.yaml` 설정을 자동으로 읽어 웹 서버를 구축하고 무상태 서비스를 배포 및 구동합니다.
