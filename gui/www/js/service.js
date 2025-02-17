DRApp.route("home", "/", "Home", "Base", "home");

DRApp.models = DRApp.rest("GET", "api/model")["models"];

DRApp.attach();
