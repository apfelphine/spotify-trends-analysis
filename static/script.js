// State
let selectedMode = "popularity";
let currentSelectedResourceId = null
let availableResourceIds = {}
let selectedResourceType = "artist"
let legend = null;
let minDate = null;
let maxDate = null;

// Map
const map = L.map('map').setView([51.505, -0.09], 2);
const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 2,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    noWrap: true
}).addTo(map);

// HTML Elements
const resourceSelectorElement = document.getElementById('resourceInput');
const modeSelectionElement = document.getElementById('modeSelection');
const updateDataButtonElement = document.getElementById('updateData');

// Initialize Materialize
M.Collapsible.init(document.getElementById('errorDetailCollapsible'), {});
M.FormSelect.init(resourceSelectorElement, {});
let modeSelectionInstance = M.FormSelect.init(modeSelectionElement, {});
const errorModalInstance = M.Modal.init(document.getElementById('error-modal'), {});

const startDateInstance =  M.Datepicker.init(document.getElementById('startDate'), {
    autoClose: true,
    showClearBtn: true,
    openByDefault: false,
    onClose: onUpdateStartDate
})
const endDateInstance = M.Datepicker.init(document.getElementById('endDate'), {
    autoClose: true,
    showClearBtn: true,
    openByDefault: false,
    onClose: onUpdateEndDate
})
const autoCompleteInstance = M.Autocomplete.init(document.getElementById('resourceIdInput'), {
    data: {},
    minLength: 3,
    limit: 10,
    onAutocomplete: onAutocompleteResourceId,
});

// Event Listeners
updateDataButtonElement.addEventListener(
    'click', function (event) {
        updateMap();
    }
)

resourceSelectorElement.addEventListener(
    'change', function (event) {
        if (this.value === selectedResourceType) {
            return
        }
        selectedResourceType = this.value

        // Update and re-init mode selection
        document.getElementById("popularityOption").innerText = `Popularity of specific ${selectedResourceType}`
        document.getElementById("trendsOption").innerText = `Most popular ${selectedResourceType} per country`
        modeSelectionInstance = M.FormSelect.init(modeSelectionElement, {});

        if (selectedMode === "popularity") {
            fetchAvailableResources()
        }
        updateButtonEnabled()
    }
)

modeSelectionElement.addEventListener(
    'change', function (event) {
        if (this.value === selectedMode) {
            return
        }
        selectedMode = this.value

        const resourceInputSection =  document.getElementById("resourceInputSection");
        if (selectedMode === "popularity") {
            fetchAvailableResources()
            resourceInputSection.style.display = 'block';
        } else {
            resourceInputSection.style.display = 'none';
            resetSelectedResourceId()
        }
        updateButtonEnabled()
    }
)

// Initialize datepicker
fetchJSON(`http://localhost:8080/api/data/imported-date-range`)
    .then(data => {
        minDate = new Date(data["from"])
        maxDate = new Date(data["to"])
        startDateInstance.options["minDate"] = minDate
        startDateInstance.options["maxDate"] = maxDate
        endDateInstance.options["minDate"] = minDate
        endDateInstance.options["maxDate"] = maxDate
    })

// Initialize available resources
fetchAvailableResources();

// Utility
function onUpdateStartDate() {
    endDateInstance.options["minDate"] = startDateInstance.date ? startDateInstance.date : minDate
}
function onUpdateEndDate() {
    startDateInstance.options["maxDate"] = endDateInstance.date ? endDateInstance.date : maxDate
}

function onAutocompleteResourceId(selectedResource) {
    selectedResource = selectedResource.trim()
    if (selectedResource.length > 0) {
        selectedResource = availableResourceIds[selectedResource];
        if (selectedResource === currentSelectedResourceId) {
            return
        }
        currentSelectedResourceId = selectedResource;
    }

    updateButtonEnabled()
}

function fetchJSON(url, errorMessage) {
    return fetch(url)
        .then(response => {
            if (!response.ok) {
                const errorMessageElement = document.getElementById('error-message');
                errorMessageElement.innerText = errorMessage;
                const errorDetailsElement = document.getElementById('error-details');
                errorDetailsElement.innerHTML = `Failed to fetch <a href="${url}">${url}</a> \n[Statuscode: ${response.status}]`;
                errorModalInstance.open()
                throw new Error(`Failed to fetch ${url}`);
            }
            return response.json();
        });
}

function disableAllInputs() {
    document.getElementById("input-panel")
        .querySelectorAll("button, input, select")
        .forEach(el => {
            el.disabled = true;
        });
}

function enableAllInputs() {
    document.getElementById("input-panel")
        .querySelectorAll("button, input, select")
        .forEach(el => {
            el.disabled = el !== updateDataButtonElement ? false : !canFetchData();
        });
}

function updateButtonEnabled() {
    updateDataButtonElement.disabled = !canFetchData();
}

function canFetchData() {
    return selectedMode === "trends" || currentSelectedResourceId !== null
}

function dateToString(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are 0-based
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}Z`;
}

function resetSelectedResourceId() {
    autoCompleteInstance.activeIndex = -1;
    autoCompleteInstance.el.value = null;
    currentSelectedResourceId = null;
    document.getElementById('resourceIdInputLabel').classList.remove("active");
}

function fetchAvailableResources() {
    // Reset input
    resetSelectedResourceId()

    // Set correct label
    document.getElementById("resourceIdInputLabel").textContent = `Enter ${selectedResourceType} to analyse`

    // Loading indication
    const loadingIndicator = document.getElementById('selectionLoadingIndicator');
    loadingIndicator.style.display = 'block';

    // Disable inputs
    disableAllInputs()

    fetchJSON(`http://localhost:8080/api/${selectedResourceType}s`,
        `Could not load available ${selectedResourceType}s.`)
        .then(data => {
            availableResourceIds = data.reduce((acc, res, _) => {
                let name = selectedResourceType === "artist" ? res.name : res.name + " (" + res.artists.map(item => item.name).join(", ") + ")"
                acc[name] = res.id;
                return acc;
            }, {});
            const dict = data.reduce((acc, res, _) => {
                let name = selectedResourceType === "artist" ? res.name : res.name + " (" + res.artists.map(item => item.name).join(", ") + ")"
                acc[name] = selectedResourceType === "track" ? res.album.image_url : res.image_url;
                return acc;
            }, {});
            autoCompleteInstance.updateData(dict);

        })
        .catch(error => console.error(`Error loading ${selectedResourceType}:`, error))
        .finally(() => {
            loadingIndicator.style.display = 'none';
            enableAllInputs();
            updateButtonEnabled();
        });
}

function addPopularityData(data) {
    function getColor(popularity) {
        // const baseGreen = { r: 29, g: 185, b: 84 }; // Spotify green
        const baseGreen = {r: 29, g: 150, b: 60};  // Slightly darker spotify green

        const white = {r: 255, g: 255, b: 255};

        const r = Math.round(white.r + (baseGreen.r - white.r) * popularity);
        const g = Math.round(white.g + (baseGreen.g - white.g) * popularity);
        const b = Math.round(white.b + (baseGreen.b - white.b) * popularity);

        return `rgb(${r}, ${g}, ${b})`;
    }


    L.geoJSON(data, {
        style: function (feature) {
            return {
                fillColor: getColor(feature.properties.popularity),
                color: "#000",
                weight: 1,
                fillOpacity: 0.8
            }
        },
        onEachFeature: function (feature, layer) {
            let popularity = feature.properties.popularity;
            if (Math.floor(popularity * 10000) !== popularity * 10000) {
                popularity = popularity.toFixed(4);
            } else {
                popularity = popularity.toString();
            }
            const popupContent = `
                    <strong>${feature.properties.name} (${feature.properties.alpha_2_code})</strong><br>
                    Popularity: ${popularity}
                `;
            layer.bindPopup(popupContent);
        }
    }).addTo(map);

    legend.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend'),
            grades = [0, 0.25, 0.5, 0.75, 1];

        div.innerHTML = `
            <div class="legend-title"><b>Relative Popularity Of "${autoCompleteInstance.el.value}"</b></div>
        `
        for (var i = 0; i < grades.length; i++) {
            div.innerHTML += '<i class="color" style="background:' + getColor(grades[i]) + '"></i> ' + grades[i];

            if (i === grades.length -1) {
                div.innerHTML += " (most popular)"
              } else {
                div.innerHTML += ' &ndash; ' + grades[i + 1]

                if (i === 0) {
                    div.innerHTML += " (least popular)"
                }
            }


            div.innerHTML += "<br>"
        }

        div.innerHTML += "<div style='margin-top: 5px'><i>" +
            "The values are scaled so that the country with the highest " +
            "total ranking receives a value of 1." +
            "</i></div>"

        return div;
    };
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function addTrendData(data) {
    const nameCounts = data.features.reduce((acc, feature) => {
    const name = feature.properties[selectedResourceType].name;
        acc[name] = (acc[name] || 0) + 1;
        return acc;
    }, {});
    const names = Object.keys(nameCounts).sort((a, b) => nameCounts[b] - nameCounts[a]);

    const paletteName = names.length > 11 ? "mpn65" : "cb-Paired"
    let paletteDict  = {}
    var generatedPalette = palette(paletteName, names.length);
    for (var i = 0; i < names.length; i++) {
        paletteDict[names[i]] = generatedPalette[i]
    }

    L.geoJSON(data, {
        style: function (feature) {
            return {
                fillColor: "#" + paletteDict[feature.properties[selectedResourceType].name],
                color: "#000",
                weight: 1,
                fillOpacity: 0.8
            }
        },
        onEachFeature: function (feature, layer) {
            const res = feature.properties[selectedResourceType]
            const url = selectedResourceType === "track" ? res.album.image_url : res.image_url

            let details = ""
            if (selectedResourceType === "track") {
                let albumType = res.album.album_type !== "album" ? ` (${capitalize(res.album.album_type)})` : ""
                let artistLabel = res.artists.length > 1 ? "Artists" : "Artist";
                details = `
                    <b>Title</b>: ${res.name} <br>
                    <b>Album</b>: ${res.album.name}${albumType}<br>
                    <b>${artistLabel}</b>: ${res.artists.map(item => item.name).join(", ")}<br>
                    <audio class="center-align" controls>
                        <source src="${res.preview_url}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                `
            } else if (selectedResourceType === "album") {
                let artistLabel = res.artists.length > 1 ? "Artists" : "Artist";
                details = `
                    <b>Name</b>: ${res.name} <br>
                    <b>Type</b>: ${capitalize(res.album_type)} <br>
                    <b>Total Tracks</b>: ${res.total_tracks}<br>
                    <b>${artistLabel}</b>: ${res.artists.map(item => item.name).join(", ")}<br>
                `
            } else if (selectedResourceType === "artist") {
                details += `<b>Name</b>: ${res.name} <br>`
                if (res.genres && res.genres.length > 1) {
                    details += `
                    <b>Genres</b>: ${res.genres.join(", ")}<br>
                `
                }
            }

            const popupContent = `
                <div class="card">
                <div class="card-image">
                      <img src="${url}">
                      <span class="card-title truncate">${res.name}</span>
                      <a class="btn-floating halfway-fab waves-effect waves-light green" target="_blank" href="${res.spotify_url}">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Spotify_icon.svg/1024px-Spotify_icon.svg.png?20220821125323" alt="Spotify Icon" style="width: 30px; height: 30px;">
                    </a>
                </div>
                <div class="card-content">
                  ${details}  
                
                  <br>
                  <divider></divider>
                  <div class="country-info right-align">
                    <i>Country: <strong>${feature.properties.name} (${feature.properties.alpha_2_code})</strong></i>
                  </div>
                </div>
              </div>
                `;
            layer.bindPopup(popupContent);
        }
    }).addTo(map);

    legend.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend');
        div.style.overflowY = 'auto';
        div.style.maxHeight = '200px';

        div.innerHTML = `<div class="legend-title"><b>Most Popular ${capitalize(selectedResourceType)}</b></div>`
        names.forEach(name => {
                div.innerHTML += '<i class="color" style="background: #' + paletteDict[name] + '"></i> <strong class="truncate">' +
                name + '</strong>';
            });

        return div;
    };
}

function updateMap() {
    if (!canFetchData()) {
        return
    }

    // Disable inputs
    disableAllInputs()

    // Loading indication on map
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'block';

    // Reset & disable map
    map._handlers.forEach(function (handler) {
        handler.disable();
    });
    map.removeControl(map.zoomControl);
    map.eachLayer(layer => {
        if (layer !== tiles) map.removeLayer(layer);
    });
    map.setView([51.505, -0.09], 2);
    if (legend != null) {
        map.removeControl(legend)
        legend = null;
    }

    // Construct url
    let url = `http://localhost:8080/api/maps/${selectedMode}/${selectedResourceType}`;
    if (currentSelectedResourceId != null) {
        url += `/${currentSelectedResourceId}`
    }
    const params = new URLSearchParams();
    if (startDateInstance.date) params.append('from_date', dateToString(startDateInstance.date));
    if (endDateInstance.date) params.append('to_date', dateToString(endDateInstance.date));
    if (params.toString()) url += '?' + params.toString();

    fetchJSON(url, "Could not load map.")
        .then(data => {
            legend = L.control({position: 'topright'});
            if (selectedMode === "popularity") {
                addPopularityData(data)
            } else if (selectedMode === "trends") {
                addTrendData(data)
            }
            legend.addTo(map);
        })
        .catch(error => {
            console.log(error)
        })
        .finally(() => {
            // Re-enable inputs
            enableAllInputs()

            // Disable Button (will be re-enabled on data-change)
            updateDataButtonElement.disabled = true

            loadingIndicator.style.display = 'none';

            // Enable map
            map._handlers.forEach(function (handler) {
                handler.enable();
            });
            map.addControl(map.zoomControl);
        });
}


