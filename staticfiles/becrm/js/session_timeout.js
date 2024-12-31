function sessionTimeout(options) {
    const idleTimeout = options.idleTimeout || 600; // Default idle timeout in seconds
    const warningTimeout = options.warningTimeout || 540; // Default warning timeout in seconds
    const warningMessage = options.warningMessage || "Your session is about to expire!";
    const logoutUrl = options.logoutUrl || "/logout"; // Default logout URL
    const onTimeout = options.onTimeout || function () {
        window.location.href = logoutUrl;
    };

    let idleTime = 0;
    let warningShown = false; // Flag to track if warning has been displayed

    function resetTimer() {
        idleTime = 0;
        warningShown = false
    }

    function showWarning() {
        if (!warningShown) {
            alert(warningMessage);
            warningShown = true;
        }
    }

    // Increment idle time counter every second
    const idleInterval = setInterval(() => {
        idleTime++;
        if (idleTime >= idleTimeout - warningTimeout && idleTime < idleTimeout) {
            showWarning();
        } else if (idleTime >= idleTimeout) {
            clearInterval(idleInterval);
            onTimeout();
        }
    }, 1000);

    // Reset timer on user activity
    window.onload = resetTimer;
    window.onmousemove = resetTimer;
    window.onmousedown = resetTimer; // User clicks
    window.ontouchstart = resetTimer; // Touchscreen
    window.onclick = resetTimer; // Mouse click
    window.onkeydown = resetTimer; // Keyboard input
    window.addEventListener("scroll", resetTimer, true); // Scrolling
}
