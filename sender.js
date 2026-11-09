const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode-terminal');

function resolveJID(to) {
    if (to.includes('@')) return to;                  // already a full JID
    if (to.endsWith('@g.us')) return to;              // group JID
    if (to.includes('-') && to.length > 15) {
        return `${to}@g.us`;                          // legacy group format e.g. 1234567890-1234567890
    }
    return `${to}@s.whatsapp.net`;                    // individual number
}

async function sendMessage(to, message) {
    const { state, saveCreds } = await useMultiFileAuthState('./auth_info');

    // Fetch the current WhatsApp Web version once per run.
    // If WhatsApp still rejects with a 405 after this, replace the line below with:
    // const version = [2, 3000, 1033893291];
    const { version } = await fetchLatestBaileysVersion();

    return new Promise((resolve, reject) => {
        let sent = false;
        let sock;

        function connect() {
            sock = makeWASocket({
                auth: state,
                version,
                browser: ['Chrome', 'Windows', '110.0.5481.177'],
            });

            sock.ev.on('creds.update', saveCreds);

            sock.ev.on('connection.update', async (update) => {
                const { connection, lastDisconnect, qr } = update;

                if (qr) {
                    console.log('\nScan this QR code with WhatsApp (Linked Devices):\n');
                    qrcode.generate(qr, { small: true });
                }

                if (connection === 'open') {
                    console.log('Connected! Sending message...');
                    try {
                        const jid = resolveJID(to);
                        await sock.sendMessage(jid, { text: message });
                        console.log(`Message sent to ${jid}`);
                        sent = true;
                        await sock.end();
                    } catch (err) {
                        reject(err);
                    }
                }

                if (connection === 'close') {
                    const statusCode = new Boom(lastDisconnect?.error)?.output?.statusCode;

                    if (sent) {
                        resolve('sent');
                        return;
                    }

                    if (statusCode === DisconnectReason.loggedOut) {
                        console.error('Logged out. Delete auth_info folder and re-run.');
                        reject(new Error('Logged out'));
                    } else if (statusCode === 515 || statusCode === 428) {
                        console.log('Reconnecting...');
                        connect();
                    } else if (
                        statusCode === DisconnectReason.connectionClosed ||
                        statusCode === DisconnectReason.connectionLost ||
                        statusCode === DisconnectReason.timedOut
                    ) {
                        console.log(`Connection dropped (${statusCode}), retrying...`);
                        connect();
                    } else {
                        reject(new Error(`Connection closed with code: ${statusCode}`));
                    }
                }
            });
        }

        connect();
    });
}

const [,, to, ...messageParts] = process.argv;
const message = messageParts.join(' ');

if (!to || !message) {
    console.error('Usage: node sender.js <jid_or_number> <message>');
    console.error('  Individual : node sender.js 96170123456 "Hello!"');
    console.error('  Group      : node sender.js 120363XXXXXXXXX@g.us "Hello group!"');
    process.exit(1);
}

sendMessage(to, message)
    .then(() => {
        console.log('Done.');
        process.exit(0);
    })
    .catch((err) => {
        console.error('Error:', err.message);
        process.exit(1);
    });