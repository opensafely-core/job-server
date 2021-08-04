import React from "react";
import useStore from "../../stores/use-store";
import classes from "./Image.module.scss";

function Image() {
  const { file } = useStore();
  return <img alt="" className={classes.img} src={file.url} />;
}

export default Image;
