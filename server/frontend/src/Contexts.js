import { createContext } from 'react';


// The list of locations is used in quite a few components throughout the
// project, e.g. table of locations, drop-down to select current location to
// view, drop-down to change a headset's location, etc.  This context stores
// the location list in one place and makes it available to components.
//
// The storage of locations and implementation of setLocations is in App.js.
//
// locations is an object indexed by the location ID.
export const LocationsContext = createContext({
  locations: {},
  setLocations: () => {}
});
