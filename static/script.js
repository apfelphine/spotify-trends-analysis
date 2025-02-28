const map = L.map('map').setView([51.505, -0.09], 2);

const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

function fetchJSON(url) {
    return fetch(url)
        .then(response => response.json());
}

function fetchArtists() {
    fetchJSON('http://localhost:8080/api/artists')
        .then(data => {
            const suggestions = data.map(artist => {
                return {id: artist.id, text: artist.name, image: artist.image_url};
            });

            // Initialize Materialize Autocomplete
            const inputElement = document.getElementById('artistInput');
            M.Autocomplete.init(inputElement, {
                data: suggestions,
                minLength: 3,
                isMultiSelect: false,
                onAutocomplete: function (selectedArtists) {
                    if (selectedArtists.length > 0) {
                        updateMap(selectedArtists[0]["id"]); // Update map when an artist is selected
                    }
                },
                onSearch: (text, autocomplete) => {
                    const filteredData = autocomplete.options.data.filter(item => {
                      return item["text"].toLowerCase().indexOf(text.toLowerCase()) >= 0;
                    });
                    autocomplete.setMenuItems(filteredData);
                }
            });
        })
        .catch(error => console.error("Error loading artists:", error));
}

 document.addEventListener('DOMContentLoaded', function() {
    fetchArtists();
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

function updateMap(artistId) {
    const artistSelect = document.getElementById('artistInput');
    artistSelect.disabled = true;
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'block';

    map._handlers.forEach(function(handler) {
        handler.disable();
    });

    map.eachLayer(layer => {
        if (layer !== tiles) map.removeLayer(layer);
    });

    fetchJSON(`http://localhost:8080/api/maps/popularity/artist/${artistId}`)
        .then(data => {
            L.geoJSON(data, {
                style: getStyle,
                onEachFeature: onEachFeature
            }).addTo(map);
        })
        .catch(error => console.error("Error loading GeoJSON data:", error))
        .finally(() => {
            artistSelect.disabled = false;
            loadingIndicator.style.display = 'none';

            map._handlers.forEach(function(handler) {
                handler.enable();
            });
        });
}


