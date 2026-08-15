// Scanner helper script integrating html5-qrcode
let html5QrCode = null;

function initQrScanner(onSuccessCallback, onErrorCallback) {
    if (typeof Html5Qrcode === "undefined") {
        console.warn("Html5Qrcode library not loaded yet.");
        return;
    }

    html5QrCode = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };

    html5QrCode.start(
        { facingMode: "environment" },
        config,
        (decodedText, decodedResult) => {
            if (onSuccessCallback) onSuccessCallback(decodedText, decodedResult);
        },
        (errorMessage) => {
            if (onErrorCallback) onErrorCallback(errorMessage);
        }
    ).catch((err) => {
        console.error("Camera start error:", err);
    });
}

function stopQrScanner() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            console.log("QR Scanner stopped.");
        }).catch(err => {
            console.error("Failed to stop scanner", err);
        });
    }
}
