window.__XIXI_REMEMBERED_SAVE_DIR__ = {"firstTimeCompleted": false, "defaultSaveMode": "", "defaultSaveDir": ""};
try {
  if (window.__XIXI_REMEMBERED_SAVE_DIR__ && window.__XIXI_REMEMBERED_SAVE_DIR__.firstTimeCompleted) {
    localStorage.setItem('xixi_first_time_save_dir_done', '1');
    localStorage.setItem('xixi_has_chosen_save_dir', 'true');
    if (window.__XIXI_REMEMBERED_SAVE_DIR__.defaultSaveDir) localStorage.setItem('xixi_default_save_dir', window.__XIXI_REMEMBERED_SAVE_DIR__.defaultSaveDir);
    if (window.__XIXI_REMEMBERED_SAVE_DIR__.defaultSaveMode) localStorage.setItem('xixi_default_save_mode', window.__XIXI_REMEMBERED_SAVE_DIR__.defaultSaveMode);
  }
} catch(e) {}
