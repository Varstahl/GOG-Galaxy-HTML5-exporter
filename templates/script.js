document.addEventListener("DOMContentLoaded", function() {
    const corners     = ['tl', 'tr', 'bl', 'br'];
    const overlay     = document.getElementById('overlay');
    const controls    = document.getElementById('controls');
    const games       = document.getElementById('games');
    const gameList    = games.children;
    const gameSearch  = document.getElementById('search');
    const gameSize    = document.getElementById('width');
    const gameSpacing = document.getElementById('spacing');

    var X = 0,                          // Last known horizontal position
        Y = 0,                          // Last known vertical position
        bCursorShow = true,             // Should the cursor be shown again?
        lastElement = {'id': null};     // Last element with an active tooltip

    /* Python equivalent of string formatting */
    String.prototype.format = function() {
        var args = arguments;
        this.unkeyed_index = 0;
        return this.replace(/\{(\w*)\}/g, function(match, key) { 
            if (key === '') {
            key = this.unkeyed_index;
            this.unkeyed_index++
            }
            if (key == +key) {
                return args[key] !== 'undefined' ? args[key] : match;
            } else {
                for (var i = 0; i < args.length; i++) {
                    if (typeof args[i] === 'object' && typeof args[i][key] !== 'undefined') {
                        return args[i][key];
                    }
                }
                return match;
            }
        }.bind(this));
    };

    function updateTooltipPos(x, y) {
        if (updateTooltipPos.tooltip) {
            const t = updateTooltipPos.tooltip;
            const w = document.documentElement.clientWidth || document.body.clientWidth;
            const h = document.documentElement.clientHeight || document.body.clientHeight;

            // Anchor the tooltip to the right/bottom if the standard orientation overflows
            // the view, and there's enough space to fit it in the other direction.
            const bRight = (w < (x + t.offsetWidth)) && (0 <= (x - t.offsetWidth));
            const bBottom = (h < (y + t.offsetHeight)) && (0 <= (y - t.offsetHeight));
            const pos = bRight + 2 * bBottom;  // Boolean to bit scalar
            var newX = x - (bRight ? t.offsetWidth : 0);
            var newY = y - (bBottom ? t.offsetHeight : 0);
            Object.assign(t.style, {left: newX + 'px', top: newY + 'px'});

            for (var i = 0; i < 4; i++) {
                t.classList[i == pos ? 'add' : 'remove'](corners[i]);
            }
        }
    }

    // Return the child element that acts as a tooltip
    function getTooltip(element) {
        for (const child of element.children)
            if (child.classList.contains("data"))
                return child;
        return null;
    }

    /* Set the `min-width` equal to the current width 

       We use `display: none` instead of hiding in order to save
       a lot of time on loading. In order to have both the minimum
       necessary blank space and tooltips not resizing along the edges
       of the screen, we temporarily display & hide to calculate the
       necessary width, before resetting both */
    function initTooltip(element) {
        element.style.visibility = 'hidden';
        element.style.display = 'block';
        element.style.minWidth = element.offsetWidth + 'px';
        element.style.display = null;
        element.style.visibility = null;
    }

    // Wrapper for the continuous update of the range input controls
    function hookRangeChange(r,f) {
        var n,c,m;
        r.addEventListener("input",function(e){n=1;c=e.target.value;if(c!=m)f(e);m=c;});
        r.addEventListener("change",function(e){if(!n)f(e);});
    }

    // Update the game card width
    function onChangeSize(event) {
        games.style.setProperty('--cover-width', event.target.value + 'px');
    }

    // Update the game cards spacing
    function onChangeSpacing(event) {
        games.style.setProperty('--cover-spacing', event.target.value + 'px');
    }

    // Show/hide the input controls
    function onToggleControls(event) {
        if (event.ctrlKey) {
            if (32 == event.keyCode) {
                controls.classList.toggle('visible');  // Ctrl+Space
            } else if (70 == event.keyCode) {
                controls.classList.add('visible');  // Ctrl+F
            }

            // Focus on the search bar, if visible
            if (controls.classList.contains('visible'))
                gameSearch.focus();
        }
    }

    // Triggers `onSearch` to clear the search results
    function onSearchCancel(event) {
        setTimeout(onSearch, 10, event);
    }

    // Perform search on the games
    function onSearch(event) {
        var query = event.target.value.toLowerCase().replace(/^\s+|\s+$/g, '').replace(/\s{2,}/g, ' ');
        if (query == onSearch.lastQuery)
            return;
        onSearch.lastQuery = query;
        const bCancelSearch = 0 == query.length;
        games.classList.toggle('search-results', !bCancelSearch);

        if (bCancelSearch) {
            // Reset search results
            for (const o of onSearch.results) {
                gameList[o].classList.remove('hit');
                gameList[o].style.order = null;
            }
            onSearch.results = []
        } else {
            // Build a list of results
            const filteredQuery = query.replace(/\s+/, '.*?');
            var results = [];
            for (var i = 0; i < gameList.length; i++) {
                const searchData = JSON.parse(gameList[i].dataset.search);
                for (const source of searchData) {
                    if (-1 !== source.search(filteredQuery)) {
                        results.push(i);
                        break;
                    }
                }
            }
            // In with the new…
            for (const n of results) {
                if (!onSearch.results.includes(n)) {
                    gameList[n].classList.add('hit');
                    //gameList[o].style.order = /* for future weighted searches */
                }
            }
            // … out with the old
            for (const o of onSearch.results) {
                if (!results.includes(o)) {
                    gameList[o].classList.remove('hit');
                    gameList[o].style.order = null;
                }
            }
            onSearch.results = results;
        }
    }
    onSearch.results = [];  // Init static variable

    // Raycasting for easier tooltip management
    function onMouseEvent(event) {
        // Update coordinates on `mousemove` events
        if ('mousemove' === event.type) {
            X = event.offsetX;
            Y = event.offsetY;
        }

        // Based on current mouse coordinates find the relative game card
        var element = {'id': null};
        if ('mouseout' !== event.type) {
            const elements = document.elementsFromPoint(X, Y);
            // .overlay #game-ID html
            if (3 == elements.length)
                element = elements[1];
        }

        if (element.id == lastElement.id) {
            // We're on the same card as before, update the tooltip position only
            if (element.id)
                updateTooltipPos(X, Y);
        } else {
            // We're not on the same card as before, hide previous card's tooltip
            if (lastElement.id) {
                lastElement.classList.remove('hover');
                setTimeout(function(){
                    if (bCursorShow)
                        overlay.style.cursor = 'initial';
                }, 100);
                bCursorShow = true;
                updateTooltipPos.tooltip = null;
            }

            // If we're on a game card, show its tooltip
            if (element.id) {
                const t = getTooltip(element);
                updateTooltipPos.tooltip = t;
                if ('' === t.style.visibility)
                    initTooltip(t);
                t.style.visibility = 'hidden';
                updateTooltipPos(X, Y);
                bCursorShow = false;
                overlay.style.cursor = 'none';
                element.classList.add('hover');
                // Delay the visualisation to remove glitches
                setTimeout(function(e) {e.style.visibility = 'visible';}, 1, t);
            }

            lastElement = element;
        }
    }

    // Setup the handlers
    overlay.addEventListener('mousemove', onMouseEvent);
    overlay.addEventListener('mouseout', onMouseEvent);
    window.addEventListener('scroll', onMouseEvent);
    document.addEventListener('keyup', onToggleControls);
    hookRangeChange(gameSize, onChangeSize);
    hookRangeChange(gameSpacing, onChangeSpacing);
    gameSearch.addEventListener('blur', onSearchCancel);
    gameSearch.addEventListener('input', onSearch);

    // Replace the SVG icon placeholders in reverse order to avoid position inconsistencies and skipped icons
    (function replaceSVGplaceholders() {
        p = {}  // cache
        // class="pi pi-[platformName]"
        const icons = document.getElementsByClassName('pi');
        for (var i = icons.length-1; 0 <= i; i--) {
            const platform = icons[i].classList[1].substr(3);
            const platforms = Array.from(icons[i].classList).slice(1).join(' ');
            try {
                if (!p.hasOwnProperty(platform)) {
                    // Maintain the symbols' view box and aspect ratios
                    const symbol = document.getElementById('icon-platform-' + platform);
                    p[platform] = '<svg class="platforms {1}" preserveAspectRatio="{2}" viewBox="{3}"><use xlink:href="#icon-platform-{0}" /></svg>'.format(
                        platform,
                        platforms,
                        symbol.getAttribute('preserveAspectRatio'),
                        symbol.getAttribute('viewBox'),
                    );
                }
                icons[i].outerHTML = p[platform];
            } catch(e) {}
        }
    })();

    // Load finished, animate the game list in
    overlay.style.opacity = 0;
    overlay.style.cursor = 'initial';
});