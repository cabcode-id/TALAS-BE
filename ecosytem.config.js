module.exports = {
  apps: [
    {
      name: "talas-be",
      cwd: "/home/ubuntu/TALAS-BE",

      script: "/home/ubuntu/TALAS-BE/.venv/bin/python3",
      args: "run.py",
      interpreter: "none",

      watch: false,
      autorestart: true,
      max_restarts: 5,

      env_file: "/home/ubuntu/TALAS-BE/.env",

      out_file: "/home/ubuntu/.pm2/logs/talas-be-out.log",
      error_file: "/home/ubuntu/.pm2/logs/talas-be-error.log",
    },
  ],
};
