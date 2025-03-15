# reusable-workflows-library

A React component for displaying a galactic map.

<p>
  <a href="https://github.com/outoforbitdev/reusable-workflows-library/actions?query=workflow%3ATest+branch%3Amaster">
    <img alt="Test build states" src="https://github.com/outoforbitdev/reusable-workflows-library/workflows/Test/badge.svg">
  </a>
  <a href="https://github.com/outoforbitdev/reusable-workflows-library/actions?query=workflow%3ATest+branch%3Amaster">
    <img alt="Release build states" src="https://github.com/outoforbitdev/reusable-workflows-library/workflows/NPM Publish/badge.svg">
  </a>
  <a href="https://securityscorecards.dev/viewer/?uri=github.com/outoforbitdev/reusable-workflows-library">
    <img alt="OpenSSF Scorecard" src="https://api.securityscorecards.dev/projects/github.com/outoforbitdev/reusable-workflows-library/badge">
  </a>
  <a href="https://github.com/outoforbitdev/reusable-workflows-library/releases/latest">
    <img alt="Latest github release" src="https://img.shields.io/github/v/release/outoforbitdev/reusable-workflows-library?logo=github">
  </a>
  <a href="https://github.com/outoforbitdev/reusable-workflows-library/issues">
    <img alt="Open issues" src="https://img.shields.io/github/issues/outoforbitdev/reusable-workflows-library?logo=github">
  </a>
</p>

## Features
- Display planets and spacelanes on a galactic map
- Map is both draggable and zoomable on desktop and mobile
  - Single finger drag and pinch to zoom on mobile
  - Click and drag and scroll to zoom on desktop
- Customize the colors
- Automatically adjusts colors based on themes
- Add custom options for the user to modify the map

## Installation
```
npm install --save @outoforbitdev/galaxy-map
```

## Usage
Import:

`import GalaxyMap, {MapColor} from "@outoforbitdev/galaxy-map";`

Create:

```typescript
const planets =[
  {
    name: "Earth",
    x: 100,
    y: 0,
    color: MapColor.Blue,
    focusLevel: 1,
  },
  {
    name: "Kepler-37",
    x: 200,
    y: 300,
    color: MapColor.Red,
    focusLevel: 2,
  }
]

const spaceLanes = [
  {
    name: "Earth-Kepler Route",
    xOne: 100,
    yOne: 0,
    xTwo: 200,
    yTwo: 300,
    color: MapColor.Gray,
    focusLevel: 2,
  }
]

const dimensions = {
  minX: -100,
  minY: -100,
  maxX: 400,
  maxY: 400,
}

const zoom = {
  initial: 80,
  min: 0,
}

return (
  <GalaxyMap
    planets={planets}
    spacelanes={spacelanes}
    dimensions={dimensions}
    zoom={zoom}
  />
);
```

## API
### Component Props

| Prop              | Type            | Default   | Description |
| ----------------- | --------------- | --------- | ----------- |
| `planets`         | `IPlanet[]`     | Required  | List of planets to display on the map |
| `spacelanes`      | `ISpacelane[]`  | Required  | List of spacelanes to display on the map |
| `dimensions.minX` | `number`        | Required  | Minimum x coordinate that should be displayed |
| `dimensions.minY` | `number`        | Required  | Minimum y coordinate that should be displayed |
| `dimensions.maxX` | `number`        | Required  | Maximum x coordinate that should be displayed |
| `dimensions.maxY` | `number`        | Required  | Maximum y coordinate that should be displayed |
| `mapOptions`      | `IMapOptions[]` | `[]`      | Options for the options window in the map |
| `zoom.initial`    | `number`        | `1`       | Initial zoom level for the map |
| `zoom.min`        | `number`        |           | Minimum zoom level |
| `zoom.max`        | `number`        |           | Maximum zoom level |

### IPlanet Props
| Prop          | Type        | Default   | Description |
| ------------- | ----------- | --------- | ----------- |
| `name`        | `string`    | Required  | Name of the planet |
| `x`           | `number`    | Required  | X coordinate of the planet |
| `y`           | `number`    | Required  | Y coordinate of the planet |
| `color`       | `MapColor`  | Required  | Color of the planet |
| `focusLevel`  | `number`    | Required  | Zoom level at which the planet comes into focus

### ISpacelane Props
| Prop          | Type        | Default   | Description |
| ------------- | ----------- | --------- | ----------- |
| `name`        | `string`    | Required  | Name of the spacelane |
| `xOne`        | `number`    | Required  | X coordinate of the first end of the spacelane |
| `yOne`        | `number`    | Required  | Y coordinate of the first end of the spacelane |
| `xTwo`        | `number`    | Required  | X coordinate of the second end of the spacelane |
| `yTwo`        | `number`    | Required  | Y coordinate of the second end of the spacelane |
| `color`       | `MapColor`  | Required  | Color of the spacelane |
| `focusLevel`  | `number`    | Required  | Zoom level at which the spacelane comes into focus |

### IMapOptionsProps
| Prop                  | Type          | Default | Description |
| --------------------- | ------------- | ------- | ----------- |
| `hidePlanetLabels`    | `boolean`     | `false` | Whether to hide planet text labels at all zoom levels |
| `hideSpacelaneLabels` | `boolean`     | `false` | Whether to hide spacelane text labels at all zoom levels |
| `showAllPlanets`      | `boolean`     | `false` | Whether to show all planets at all zoom levels |
| `showAllSpacelanes`   | `boolean`     | `false` | Whether to show all spacelanes at all zoom levels |
| `customOptions`       | `MapOption[]` | `[]`    | Additional options to show in the options window |

### MapOption Props
| Prop            | Type                | Default   | Description |
| -------------   | -----------         | --------- | ----------- |
| `currentValue`  | `boolean`           | Required  | Current value of the option |
| `setValue`      | `(boolean) => void` | Required  | Callback when the value of the option is changed |
| `label`         | `string`            | Required  | Text label for the option |
| `inputType`     | `string`            | Required  | Input type for the input element of the option |
