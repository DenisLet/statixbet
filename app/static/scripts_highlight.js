document.addEventListener('DOMContentLoaded', (event) => {
    // Create and style toast
    const toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast';
    toast.innerHTML = `<p>The team positions have changed - you need to update the odds data.</p>`;
    document.body.appendChild(toast);

    const style = document.createElement('style');
    style.innerHTML = `
        /* Toast styles */
        .toast {
            visibility: hidden;
            min-width: 250px;
            margin-left: -125px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 2px;
            position: fixed;
            z-index: 1;
            left: 50%;
            bottom: 30px;
            font-size: 17px;
            box-shadow: 0px 0px 10px 0px rgba(0,0,0,0.2);
            padding: 16px;
        }

        .toast.show {
            visibility: visible;
            -webkit-animation: fadein 0.5s, fadeout 0.5s 2.5s;
            animation: fadein 0.5s, fadeout 0.5s 2.5s;
        }

        @-webkit-keyframes fadein {
            from {bottom: 0; opacity: 0;}
            to {bottom: 30px; opacity: 1;}
        }

        @keyframes fadein {
            from {bottom: 0; opacity: 0;}
            to {bottom: 30px; opacity: 1;}
        }

        @-webkit-keyframes fadeout {
            from {bottom: 30px; opacity: 1;}
            to {bottom: 0; opacity: 0;}
        }

        @keyframes fadeout {
            from {bottom: 30px; opacity: 1;}
            to {bottom: 0; opacity: 0;}
        }
    `;
    document.head.appendChild(style);

    // Function to add highlight class
    function addHighlight(element) {
        element.classList.add('highlight');
        setTimeout(() => {
            element.classList.remove('highlight');
        }, 500);
    }

    // Function to swap labels
    function swapLabels() {
        const whereSelect = document.getElementById('where');
        const team1WinLabel = document.getElementById('team1-win-label');
        const team1LossLabel = document.getElementById('team1-loss-label');

        if (whereSelect.value === 'HOME') {
            if (!team1WinLabel.classList.contains('highlight') && !team1LossLabel.classList.contains('highlight')) {
                addHighlight(team1WinLabel);
                addHighlight(team1LossLabel);

                setTimeout(() => {
                    team1WinLabel.textContent = 'Win Odds (TEAM):';
                    team1LossLabel.textContent = 'Win Odds (OPPONENT):';

                    toast.className = 'toast show';
                    setTimeout(() => {
                        toast.className = toast.className.replace('show', '');
                    }, 3000);
                }, 500);
            }
        } else if (whereSelect.value === 'AWAY') {
            if (!team1WinLabel.classList.contains('highlight') && !team1LossLabel.classList.contains('highlight')) {
                addHighlight(team1WinLabel);
                addHighlight(team1LossLabel);

                setTimeout(() => {
                    team1WinLabel.textContent = 'Win Odds (OPPONENT):';
                    team1LossLabel.textContent = 'Win Odds (TEAM):';

                    toast.className = 'toast show';
                    setTimeout(() => {
                        toast.className = toast.className.replace('show', '');
                    }, 3000);
                }, 500);
            }
        }
    }

    document.getElementById('where').addEventListener('change', swapLabels);
});
