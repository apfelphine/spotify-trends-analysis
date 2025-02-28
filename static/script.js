// State
let currentSelectedArtist = null
let currentStartDate = null
let currentEndDate = null

// Background Map
const map = L.map('map').setView([51.505, -0.09], 2);

const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);


// Utility Functions
function fetchJSON(url) {
    return fetch(url)
        .then(response => response.json());
}

function fetchArtists() {
    fetchJSON('http://localhost:8080/api/artists')
        .then(data => {
            const artistIds = data.reduce((acc, artist, _) => {
                acc[artist.name] = artist.id;
                return acc;
            }, {});
            const dict = data.reduce((acc, artist, _) => {
                acc[artist.name] = artist.image_url;
                return acc;
            }, {});

            // Initialize Materialize Autocomplete
            const inputElement = document.getElementById('artistInput');
            M.Autocomplete.init(inputElement, {
                data: dict,
                minLength: 3,
                limit: 10,
                onAutocomplete: function (selectedArtist) {
                    if (selectedArtist.trim().length > 0) {
                        currentSelectedArtist = artistIds[selectedArtist.trim()];
                        updateMap(currentSelectedArtist); // Update map when an artist is selected
                    }
                },
            });
        })
        .catch(error => console.error("Error loading artists:", error));
}

document.addEventListener('DOMContentLoaded', function() {
    fetchArtists();

    var elems = document.querySelectorAll('.datepicker');
    M.Datepicker.init(elems, {
        showClearBtn: true,
        openByDefault: false,
        format: 'yyyy-mm-dd'
    });

    document.getElementById('startDate').addEventListener(
        'change', function (event) {
            currentStartDate = event.target.value;
            updateMap();
        }
    );
    document.getElementById('endDate').addEventListener(
        'change', function (event) {
            currentEndDate = event.target.value;
            updateMap();
        }
    );
});

function getStyle(feature) {
    const pop = feature.properties.popularity;
    const shade = Math.round(255 * (1 - pop));

    return {
        fillColor: `rgb(${shade}, ${shade}, ${shade})`,
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
    // Disable inputs
    const datepickers = document.querySelectorAll('.datepicker');
    datepickers.forEach(datepicker => datepicker.disabled = true);
    const artistSelect = document.getElementById('artistInput');
    artistSelect.disabled = true;
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'block';
    map._handlers.forEach(function(handler) {
        handler.disable();
    });

    // Remove old popularity layer
    map.eachLayer(layer => {
        if (layer !== tiles) map.removeLayer(layer);
    });

    // Construct url
    let url = `http://localhost:8080/api/maps/popularity/artist/${currentSelectedArtist}`;
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
            datepickers.forEach(datepicker => datepicker.disabled = false);
            loadingIndicator.style.display = 'none';

            map._handlers.forEach(function(handler) {
                handler.enable();
            });
        });
}


