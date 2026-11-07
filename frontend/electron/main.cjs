const { app, BrowserWindow } = require("electron");
const path = require("path");

const APP_URL = "https://YOUR-FRONTEND-DOMAIN.vercel.app";

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 900,
    minHeight: 650,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  if (app.isPackaged) win.loadURL(APP_URL);
  else win.loadURL("http://127.0.0.1:5173");
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
