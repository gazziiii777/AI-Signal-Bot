module.exports = {
    apps: [
        {
            name: "AI-Signal-Bot",
            script: "./main.py",
            interpreter: "./.venv/bin/python3",
            cwd: "/root/scripts/AI-Signal-Bot",
            watch: false,
            error_file: "/root/.pm2/logs/AI-Signal-Bot-error.log",
            out_file: "/root/.pm2/logs/AI-Signal-Bot-out.log",
            pid_file: "/root/.pm2/pids/AI-Signal-Bot.pid",
            exec_mode: "fork",
            env: {
                NODE_ENV: "production",
            },
            log_date_format: "YYYY-MM-DD HH:mm:ss",
            max_size: "10M",
            merge_logs: true,
            // cron_restart: "0 6 * * *", // Убрано, чтобы скрипт никогда не перезапускался
            autorestart: false
        },
    ],
};