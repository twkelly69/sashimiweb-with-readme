# sashimiweb-with-readme

這個專案會把 `restaurant_119HW.csv` 內的餐廳資料轉成 GitHub Pages 的靜態網站，每家餐廳都有自己的獨立頁面。

## 如何產生網站

1. 安裝 Python 3.11+（系統已內建，不需要額外套件）。
2. 執行下列指令，會讀取 CSV 並在 `docs/` 目錄生成首頁與每間餐廳的頁面：

   ```bash
   python generate_site.py
   ```

3. 新增或修改 CSV 後，重新執行上述指令即可重新產生所有頁面。

## 部署到 GitHub Pages

1. 在 GitHub 專案設定的 **Pages** 中，Source 選擇 **Deploy from a branch**。
2. Branch 選擇 `main`，資料夾選擇 `/docs`。
3. 儲存後 GitHub 會自動部署，首頁位於 `<你的使用者名稱>.github.io/<repo 名稱>/`，每間餐廳的獨立頁面都會在 `/restaurants/<slug>/` 路徑下。
