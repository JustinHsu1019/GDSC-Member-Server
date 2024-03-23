# GDSC NCCU - MemberWeb Backend

## API 說明文件

### Google 登入
- 方法: POST
- URL: `https://gdscmemberweb.pythonanywhere.com/google_login`
- 描述: 使用 Google 帳號登入系統。用戶在前端頁面通過 Google 登入後，將接收到一個 ID Token，然後將此 Token 作為身份驗證信息發送到後端並產生 JWT。詳細的實踐方法可參考 [Login Test: index.html](https://github.com/gdscnccu/member-server/blob/main/Scripts/Login_Test/index.html) 裡面有可實際登入並呼叫此 API 的 Demo 頁面，同時裡面的 [Client ID](162429496765-ortobcqq28giqurc67ls7adv5ekft7mv.apps.googleusercontent.com) 就是目前正式環境所使用的
- Headers:
  - Key: `Content-Type`
  - Value: `application/json`
- Body (raw, JSON):
  ```json
  {
    "idToken": "<由 Google 帳號登入後獲得的 ID Token>"
  }

### 創建 (Create)

#### 1. 創建筆記 (Create Note)
- 方法: POST
- URL: `https://gdscmemberweb.pythonanywhere.com/create`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`
- Body (raw, JSON):
  ```json
  {
    "collection": "notes",
    "data": {
      "name": "Note 1210",
      "date": "2023/11/26",
      "link": "http://gdsc.com/note1126"
    }
  }

#### 2. 創建表單 (Create Form)
- 方法: POST
- URL: `https://gdscmemberweb.pythonanywhere.com/create`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`
- Body (raw, JSON):
  ```json
  {
    "collection": "forms",
    "data": {
      "expired_at": "Sun, 05 Dec 2023 19:06:46 GMT",
      "link": "http://example.com/form",
      "name": "Form 1204"
    }
  }

#### 3. 創建專案 (Create Project)
- 方法: POST
- URL: `https://gdscmemberweb.pythonanywhere.com/create`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`
- Body (raw, JSON):
  ```json
  {
    "collection": "projects",
    "data": {
      "name": "Project_1210",
      "description": "This is a new project.",
      "slides": "http://example.com/projectslides1210",
      "team_members": [],
      "project_manager": null
    }
  }

#### 4. 創建會員 (Create Member)
- 方法: POST
- URL: `https://gdscmemberweb.pythonanywhere.com/create`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給帳號本人)>`
- Body (raw, JSON):
  ```json
  {
    "collection": "users",
    "data": {
        "name": "GDSC NCCU",
        "student_id": "123456789",
        "role": "Core",
        "payment": 200,
        "paid": true,
        "major_n_grade": "資科四",
        "projects_involved": [],
        "managed_projects": []
    }
  }

#### 5. 分配會員至專案 (Assign Member to Project)
- 方法: POST
- URL: `https://gdscmemberweb.pythonanywhere.com/assign_member_to_project`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`
- Body (raw, JSON):
  ```json
  {
    "user_email": "gdscnccu@gmail.com",
    "project_name": "Project_1210"
  }

#### 6. 分配專案經理 (Assign PM)
- 方法: POST
- URL: `https://gdscmemberweb.pythonanywhere.com/assign_pm`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`
- Body (raw, JSON):
  ```json
  {
    "user_email": "gdscnccu@gmail.com",
    "project_name": "Project_1210"
  }

### 讀取 (Read)

#### 1. 讀取所有筆記 (Read Notes)
- 方法: GET
- URL: `https://gdscmemberweb.pythonanywhere.com/read?collection=notes`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限開放給所有帳號)>`

#### 2. 讀取所有表單 (Read Forms)
- 方法: GET
- URL: `https://gdscmemberweb.pythonanywhere.com/read?collection=forms`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限開放給所有帳號)>`

#### 3. 讀取所有專案 (Read Projects)
- 方法: GET
- URL: `https://gdscmemberweb.pythonanywhere.com/read?collection=projects`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限開放給所有帳號)>`

#### 4. 讀取特定專案 (Read Project)
- 方法: GET
- URL: `https://gdscmemberweb.pythonanywhere.com/read_project/<project name>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限開放給所有帳號)>`

#### 5. 讀取所有會員 (Read Members)
- 方法: GET
- URL: `https://gdscmemberweb.pythonanywhere.com/read?collection=users`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給gdscnccu@gmail.com)>`

#### 6. 讀取特定會員 (Read Member)
- 方法: GET
- URL: `https://gdscmemberweb.pythonanywhere.com/read_member/<member email>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給帳號本人)>`

### 更新 (Update)

#### 1. 更新筆記 (Update Note)
- 方法: PUT
- URL: `https://gdscmemberweb.pythonanywhere.com/update_note/<note name>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`
- Body (raw, JSON):
  ```json
  // 可以一次更新一個欄位, 多個欄位或新增欄位
  {
    "date": "12/09"
  }

#### 2. 更新表單 (Update Form)
- 方法: PUT
- URL: `https://gdscmemberweb.pythonanywhere.com/update_form/<form name>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`
- Body (raw, JSON):
  ```json
  // 可以一次更新一個欄位, 多個欄位或新增欄位
  {
    "link": "https://google.com",
  }

#### 3. 更新專案 (Update Project)
- 方法: PUT
- URL: `https://gdscmemberweb.pythonanywhere.com/update_project/<project name>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`
- Body (raw, JSON):
  ```json
  // 可以一次更新一個欄位, 多個欄位或新增欄位
  {
    "name": "Project_1210",
    "description": "Updated project description."
  }

#### 4. 更新會員 (Update Member)
- 方法: PUT
- URL: `https://gdscmemberweb.pythonanywhere.com/update_member/<member email>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給帳號本人)>`
- Body (raw, JSON):
  ```json
  // 可以一次更新一個欄位, 多個欄位或新增欄位
  {
    "name": "ABC"
  }

### 刪除 (Delete)

#### 1. 刪除筆記 (Delete Note)
- 方法: DELETE
- URL: `https://gdscmemberweb.pythonanywhere.com/delete_note/<note name>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`

#### 2. 刪除表單 (Delete Form)
- 方法: DELETE
- URL: `https://gdscmemberweb.pythonanywhere.com/delete_form/<form name>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`

#### 3. 刪除專案 (Delete Project)
- 方法: DELETE
- URL: `https://gdscmemberweb.pythonanywhere.com/delete_project/<project name>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給 gdscnccu@gmail.com)>`

#### 4. 刪除會員 (Delete Member)
- 方法: DELETE
- URL: `https://gdscmemberweb.pythonanywhere.com/delete_member/<member email>`
- Headers:
  - Key: `Authorization`
  - Value: `<由 Google ID Token 轉換的 JWT (這個 API 的訪問權限只開放給帳號本人)>`
