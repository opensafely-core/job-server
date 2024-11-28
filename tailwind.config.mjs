import tailwindForms from "@tailwindcss/forms";
import tailwindTypography from "@tailwindcss/typography";
import { fontFamily } from "tailwindcss/defaultTheme";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./templates/**/*.html", "./assets/src/scripts/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Public Sans", ...fontFamily.sans],
      },
      colors: {
        oxford: {
          DEFAULT: "#002147",
          50: "#f1f7ff",
          100: "#cfe5ff",
          200: "#9ccaff",
          300: "#69afff",
          400: "#3693ff",
          500: "#0378ff",
          600: "#0058be",
          700: "#00397a",
          800: "#002147",
          900: "#001936",
        },
        "bn-egg": {
          DEFAULT: "#17d7e6",
          50: "#f3fdfe",
          100: "#e8fbfd",
          200: "#c5f5f9",
          300: "#a2eff5",
          400: "#5de3ee",
          500: "#17d7e6",
          600: "#15c2cf",
          700: "#11a1ad",
          800: "#0e818a",
          900: "#0b6971",
        },
        "bn-picton": {
          DEFAULT: "#40b5ff",
          50: "#f5fbff",
          100: "#ecf8ff",
          200: "#cfedff",
          300: "#b3e1ff",
          400: "#79cbff",
          500: "#40b5ff",
          600: "#3aa3e6",
          700: "#3088bf",
          800: "#266d99",
          900: "#1f597d",
        },
        "bn-royal": {
          DEFAULT: "#5971f2",
          50: "#f7f8fe",
          100: "#eef1fe",
          200: "#d6dcfc",
          300: "#bdc6fa",
          400: "#8b9cf6",
          500: "#5971f2",
          600: "#5066da",
          700: "#4355b6",
          800: "#354491",
          900: "#2c3777",
        },
        "bn-grape": {
          DEFAULT: "#5324b3",
          50: "#f6f4fb",
          100: "#eee9f7",
          200: "#d4c8ec",
          300: "#baa7e1",
          400: "#8766ca",
          500: "#5324b3",
          600: "#4b20a1",
          700: "#3e1b86",
          800: "#32166b",
          900: "#291258",
        },
        "bn-roman": {
          DEFAULT: "#9b54e6",
          50: "#faf6fe",
          100: "#f5eefd",
          200: "#e6d4f9",
          300: "#d7bbf5",
          400: "#b987ee",
          500: "#9b54e6",
          600: "#8c4ccf",
          700: "#743fad",
          800: "#5d328a",
          900: "#4c2971",
        },
        "bn-blush": {
          DEFAULT: "#ff7cff",
          50: "#fff8ff",
          100: "#fff2ff",
          200: "#ffdeff",
          300: "#ffcbff",
          400: "#ffa3ff",
          500: "#ff7cff",
          600: "#e670e6",
          700: "#bf5dbf",
          800: "#994a99",
          900: "#7d3d7d",
        },
        "bn-strawberry": {
          DEFAULT: "#ff369c",
          50: "#fff5fa",
          100: "#ffebf5",
          200: "#ffcde6",
          300: "#ffafd7",
          400: "#ff72ba",
          500: "#ff369c",
          600: "#e6318c",
          700: "#bf2975",
          800: "#99205e",
          900: "#7d1a4c",
        },
        "bn-ribbon": {
          DEFAULT: "#f20c51",
          50: "#fef3f6",
          100: "#fee7ee",
          200: "#fcc2d4",
          300: "#fa9eb9",
          400: "#f65585",
          500: "#f20c51",
          600: "#da0b49",
          700: "#b6093d",
          800: "#910731",
          900: "#770628",
        },
        "bn-flamenco": {
          DEFAULT: "#ff7c00",
          50: "#fff8f2",
          100: "#fff2e6",
          200: "#ffdebf",
          300: "#ffcb99",
          400: "#ffa34d",
          500: "#ff7c00",
          600: "#e67000",
          700: "#bf5d00",
          800: "#994a00",
          900: "#7d3d00",
        },
        "bn-sun": {
          DEFAULT: "#ffd13a",
          50: "#fffdf5",
          100: "#fffaeb",
          200: "#fff4ce",
          300: "#ffedb0",
          400: "#ffdf75",
          500: "#ffd13a",
          600: "#e6bc34",
          700: "#bf9d2c",
          800: "#997d23",
          900: "#7d661c",
        },
        "bn-straw": {
          DEFAULT: "#ffb700",
          50: "#fffbf2",
          100: "#fff8e6",
          200: "#ffedbf",
          300: "#ffe299",
          400: "#ffcd4d",
          500: "#ffb700",
          600: "#e6a500",
          700: "#bf8900",
          800: "#996e00",
          900: "#7d5a00",
        },
        "os-blue": {
          default: "#1a2544",
          50: "#e7ebf6",
          100: "#d4dbef",
          200: "#afbce1",
          300: "#8b9dd2",
          400: "#667ec4",
          500: "#4461b3",
          600: "#364d8e",
          700: "#283969",
          800: "#1a2544",
          900: "#0c111f",
          950: "#05070d",
        },
      },
      container: {
        center: true,
        padding: {
          DEFAULT: "1rem",
          sm: "1rem",
          lg: "2rem",
          xl: "3rem",
          "2xl": "3rem",
        },
      },
      transitionProperty: {
        scale: "transform",
        "scale-opacity": "transform, opacity",
        buttons: "background-color, box-shadow, color",
      },
      typography: ({ theme }) => ({
        oxford: {
          css: {
            "--tw-prose-body": theme("colors.slate[900]"),
            "--tw-prose-links": theme("colors.oxford[600]"),
            "--tw-prose-counters": theme("colors.slate[800]"),
            "--tw-prose-bullets": theme("colors.slate[800]"),
          },
        },
      }),
    },
  },
  plugins: [
    tailwindTypography,
    tailwindForms,
    ({ addBase, theme }) => {
      function extractColorVars(colorObj, colorGroup = "") {
        return Object.keys(colorObj).reduce((vars, colorKey) => {
          const value = colorObj[colorKey];

          const newVars =
            typeof value === "string"
              ? { [`--color${colorGroup}-${colorKey}`]: value }
              : extractColorVars(value, `-${colorKey}`);

          return { ...vars, ...newVars };
        }, {});
      }

      addBase({
        ":root": extractColorVars(theme("colors")),
      });
    },
  ],
};
