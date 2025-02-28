// State
let currentSelectedResourceId = null
let availableResourceIds = {}
let currentStartDate = null
let currentEndDate = null
let selectedResourceType = "artist"
var legend = null

// Background Map
const map = L.map('map').setView([51.505, -0.09], 2);

const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    minZoom: 2,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    noWrap:true
}).addTo(map);
map.setMaxBounds(  [[-90,-180],   [90,180]]  )

// Utility Functions
function fetchJSON(url) {
    return fetch(url)
        .then(response => response.json());
}

function fetchResource(resource) {
    // Reset input
    const inputElement = document.getElementById('artistInput');
    const instance = M.Autocomplete.getInstance(inputElement);
    instance.activeIndex = -1;
    instance.el.value = null;
    // Stop label from floating
    document.getElementById('artistInputLabel').classList.remove("active");

    fetchJSON(`http://localhost:8080/api/${resource}`)
        .then(data => {
            availableResourceIds = data.reduce((acc, res, _) => {
                acc[res.name] = res.id;
                return acc;
            }, {});
            const dict = data.reduce((acc, res, _) => {
                acc[res.name] = res.image_url;
                return acc;
            }, {});
            instance.updateData(dict);
        })
        .catch(error => console.error(`Error loading ${resource}:`, error));
}

document.addEventListener('DOMContentLoaded', function() {
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

    const inputElement = document.getElementById('artistInput');
    const autoCompleteInstance = M.Autocomplete.init(inputElement, {
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
    });
    fetchResource('artists');

    const resourceSelector = document.getElementById('resourceInput');
    M.FormSelect.init(resourceSelector, {});
    resourceSelector.addEventListener(
        'change', function (event) {
            if (this.value === selectedResourceType) {
                return
            }
            selectedResourceType = this.value
            fetchResource(selectedResourceType + "s")
            document.getElementById("artistInputLabel").textContent = `Enter ${String(selectedResourceType).charAt(0).toUpperCase() + String(selectedResourceType).slice(1)}`
        }
    )
});

function getColor(popularity) {
    const shade = Math.round(255 * (1 - popularity));
    return `rgb(${shade}, ${shade}, ${shade})`;
}

function getStyle(feature) {
    return {
        fillColor: getColor(feature.properties.popularity),
        color: "#000",
        weight: 1,
        fillOpacity: 0.8
    };
}


function formatPopularity(popularity) {
    if (Math.floor(popularity * 10000) !== popularity * 10000) {
        return popularity.toFixed(4);
    } else {
        return popularity.toString();
    }
}

function onEachFeature(feature, layer) {
    if (feature.properties) {
        const props = feature.properties;
        const popupContent = `
            <strong>${props.name} (${props.alpha_2_code})</strong><br>
            Popularity: ${formatPopularity(props.popularity)}
        `;
        layer.bindPopup(popupContent);
    }
}

function updateMap() {
    if (currentSelectedResourceId === null) {
        return
    }

    // Disable inputs
    const datepickers = document.querySelectorAll('.datepicker');
    datepickers.forEach(datepicker => datepicker.disabled = true);
    const artistSelect = document.getElementById('artistInput');
    artistSelect.disabled = true;
    const resourceInput = document.getElementById('resourceInput');
    resourceInput.disabled = true;
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'block';
    map.setView([51.505, -0.09], 2)
    map._handlers.forEach(function(handler) {
        handler.disable();
    });
    map.removeControl( map.zoomControl );

    // Remove old popularity layer
    map.eachLayer(layer => {
        if (layer !== tiles) map.removeLayer(layer);
    });
    if (legend != null) {
        map.removeControl(legend)
    }

    legend = L.control({position: 'bottomright'});

    legend.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info legend'),
        grades = [0, 0.05, 0.1, 0.2, 0.5, 0.75, 1];

        for (var i = 0; i < grades.length; i++) {
            div.innerHTML +=
                '<i style="background:' + getColor(grades[i])  + '"></i> ' +
                grades[i] + (grades[i + 1] ? ' &ndash; ' + grades[i + 1] + '<br>' : '+');
        }

        return div;
    };

    // Construct url
    let url = `http://localhost:8080/api/maps/popularity/${selectedResourceType}/${currentSelectedResourceId}`;
    const params = new URLSearchParams();
    if (currentStartDate) params.append('from_date', currentStartDate);
    if (currentEndDate) params.append('to_date', currentEndDate);
    if (params.toString()) url += '?' + params.toString();

    fetchJSON(url)
        .then(data => {
            L.geoJSON(data, {
                style: getStyle,
                onEachFeature: onEachFeature
            }).addTo(map);
        })
        .catch(error => console.error("Error loading GeoJSON data:", error))
        .finally(() => {
            artistSelect.disabled = false;
            resourceInput.disabled = false;
            datepickers.forEach(datepicker => datepicker.disabled = false);
            loadingIndicator.style.display = 'none';

            map._handlers.forEach(function(handler) {
                handler.enable();
            });
            map.addControl( map.zoomControl );
            legend.addTo(map);
        });
}


