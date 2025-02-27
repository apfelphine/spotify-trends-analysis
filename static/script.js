const map = L.map('map').setView([51.505, -0.09], 1);

const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

function fetchJSON(url) {
  return fetch(url)
    .then(function(response) {
      return response.json();
    });
}

function getStyle(feature) {
    const pop = feature.properties.popularity;
    const shade = Math.round(255 * (1 - pop)); // Convert 1 = dark (black) to 0 = light (white)

    return {
        fillColor: `rgb(${shade}, ${shade}, ${shade})`, // Grayscale shading
        color: "#000",  // Border color
        weight: 1,
        fillOpacity: 0.8
    };
}

fetchJSON('http://localhost:8080/api/maps/popularity/artist/4q3ewBCX7sLwd24euuV69X')
    .then(data => {
        L.geoJSON(data, {
            style: getStyle
        }).addTo(map);
    })
    .catch(error => console.error("Error loading GeoJSON data:", error));


