import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { solid, regular, brands } from '@fortawesome/fontawesome-svg-core/import.macro';

import fontawesome from '@fortawesome/fontawesome'
import {
  faBandage,
  faBiohazard,
  faBug,
  faCircle,
  faCirclePlay,
  faDoorClosed,
  faElevator,
  faExclamationTriangle,
  faFire,
  faFireExtinguisher,
  faHeadset,
  faImage,
  faLocationDot,
  faMessage,
  faPerson,
  faRadiation,
  faRightFromBracket,
  faSkull,
  faSquare,
  faStairs,
  faTruckMedical,
  faUser,
  faRobot,
  faMobileScreenButton,
  faLaptopCode
} from "@fortawesome/free-solid-svg-icons";

fontawesome.library.add(
  faBandage,
  faBiohazard,
  faBug,
  faCircle,
  faCirclePlay,
  faDoorClosed,
  faElevator,
  faExclamationTriangle,
  faFire,
  faFireExtinguisher,
  faHeadset,
  faImage,
  faLocationDot,
  faMessage,
  faPerson,
  faRadiation,
  faRightFromBracket,
  faSkull,
  faSquare,
  faStairs,
  faTruckMedical,
  faUser,
  faRobot,
  faMobileScreenButton,
  faLaptopCode
  );

// Map feature type -> FA icon
const IconMap = {
  ambulance: solid('truck-medical'),
  audio: solid('circle-play'),
  'bad-person': solid('skull'),
  biohazard: solid('biohazard'),
  door: solid('door-closed'),
  elevator: solid('elevator'),
  exit: solid('right-from-bracket'),
  extinguisher: solid('fire-extinguisher'),
  fire: solid('fire'),
  headset: solid('headset'),
  injury: solid('bandage'),
  message: solid('message'),
  object: solid('square'),
  person: solid('person'),
  photo: solid('image'),
  point: solid('circle'),
  radiation: solid('radiation'),
  stairs: solid('stairs'),
  user: solid('user'),
  warning: solid('triangle-exclamation'),
  waypoint: solid('location-dot'),
  robot: solid('robot'),
  phone: solid('mobile-screen-button'),
  editor: solid('laptop-code')
};

export default IconMap;
