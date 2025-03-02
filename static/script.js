// State
let selectedMode = "popularity";
let currentSelectedResourceId = null
let availableResourceIds = {}
let currentStartDate = null
let currentEndDate = null
let selectedResourceType = "artist"
let legend = null;

// Map
const map = L.map('map').setView([51.505, -0.09], 2).setMaxBounds([[-90, -180], [90, 180]]);
const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 2,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    noWrap: true
}).addTo(map);

// Utility Functions
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

// Initialize Materialize
const resourceSelectorElement = document.getElementById('resourceInput');
M.FormSelect.init(resourceSelectorElement, {});

const errorModalInstance = M.Modal.init(document.getElementById('error-modal'), {});
M.Collapsible.init(document.getElementById('errorDetailCollapsible'), {});

const autoCompleteInstance = M.Autocomplete.init(
    document.getElementById('resourceIdInput'),
    {
        data: {},
        minLength: 3,
        limit: 10,
        onAutocomplete: function (selectedResource) {
            selectedResource = selectedResource.trim()
            if (selectedResource.length > 0) {
                selectedResource = availableResourceIds[selectedResource];
                if (selectedResource === currentSelectedResourceId) {
                    return
                }
                currentSelectedResourceId = selectedResource;
                updateMap();
            }
        },
    }
);
let modeSelectionInstance = M.FormSelect.init(document.getElementById('modeSelection'), {});

// Event Listeners
resourceSelectorElement.addEventListener(
    'change', function (event) {
        if (this.value === selectedResourceType) {
            return
        }
        selectedResourceType = this.value
        fetchAvailableResources()
    }
)

function fetchAvailableResources() {
    // Reset input
    autoCompleteInstance.activeIndex = -1;
    autoCompleteInstance.el.value = null;
    currentSelectedResourceId = null;
    document.getElementById('resourceIdInputLabel').classList.remove("active");

    // Loading indication
    const loadingIndicator = document.getElementById('selectionLoadingIndicator');
    loadingIndicator.style.display = 'block';

    // Disable input
    const resourceIdInput = document.getElementById('resourceIdInput');
    resourceIdInput.disabled = true;

    // Set correct label
    document.getElementById("resourceIdInputLabel").textContent = `Enter ${selectedResourceType} to analyse`

    // Update and re-init mode selection
    document.getElementById("popularityOption").innerText = `Popularity of specific ${selectedResourceType}`
    document.getElementById("trendsOption").innerText = `Most popular ${selectedResourceType} per country`
    modeSelectionInstance = M.FormSelect.init(document.getElementById('modeSelection'), {});

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
            instance.updateData(dict);
        })
        .catch(error => console.error(`Error loading ${resource}:`, error))
        .finally(() => {
            loadingIndicator.style.display = 'none';
            resourceIdInput.disabled = false;
        });
}

// Initialize datepicker
fetchJSON(`http://localhost:8080/api/data/imported-date-range`)
    .then(data => {
            var elems = document.querySelectorAll('.datepicker');
            M.Datepicker.init(elems, {
                showClearBtn: true,
                openByDefault: false,
                minDate: new Date(data["from"]),
                maxDate: new Date(data["to"])
            });

            document.getElementById('startDate').addEventListener(
                'change', function (event) {
                    const val = M.Datepicker.getInstance(this).date.toISOString()
                    if (currentStartDate === val) {
                        return
                    }
                    currentStartDate = val;
                    updateMap();
                }
            );
            document.getElementById('endDate').addEventListener(
                'change', function (event) {
                    const val = M.Datepicker.getInstance(this).date.toISOString()
                    if (currentEndDate === val) {
                        return
                    }
                    currentEndDate = val;
                    updateMap();
                }
            );
        }
    )

// Initialize available resources
fetchAvailableResources();

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
            grades = [0, 0.05, 0.1, 0.2, 0.5, 0.75, 1];

        for (var i = 0; i < grades.length; i++) {
            div.innerHTML +=
                '<i style="background:' + getColor(grades[i]) + '"></i> ' +
                grades[i] + (grades[i + 1] ? ' &ndash; ' + grades[i + 1] + '<br>' : '+');
        }

        return div;
    };
}

function updateMap() {
    if (selectedMode === "popularity" && currentSelectedResourceId === null) {
        return
    }

    // Disable inputs
    const datepickers = document.querySelectorAll('.datepicker');
    datepickers.forEach(datepicker => datepicker.disabled = true);
    const resourceIdInput = document.getElementById('resourceIdInput');
    resourceIdInput.disabled = true;
    const resourceInput = document.getElementById('resourceInput');
    resourceInput.disabled = true;
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
    let url = `http://localhost:8080/api/maps/${selectedMode}/${selectedResourceType}/${currentSelectedResourceId}`;
    const params = new URLSearchParams();
    if (currentStartDate) params.append('from_date', currentStartDate);
    if (currentEndDate) params.append('to_date', currentEndDate);
    if (params.toString()) url += '?' + params.toString();

    fetchJSON(url, "Could not load map.")
        .then(data => {
            legend = L.control({position: 'bottomright'});
            if (selectedMode === "popularity") {
                addPopularityData(data)
            }
            legend.addTo(map);
        })
        .catch(error => {
            console.log(error)
        })
        .finally(() => {
            // Re-enable inputs
            resourceIdInput.disabled = false;
            resourceInput.disabled = false;
            datepickers.forEach(datepicker => datepicker.disabled = false);
            loadingIndicator.style.display = 'none';

            // Enable map
            map._handlers.forEach(function (handler) {
                handler.enable();
            });
            map.addControl(map.zoomControl);
        });
}


