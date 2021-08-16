import React from "react";
import useFile from "../../hooks/use-file";
import useStore from "../../stores/use-store";
import classes from "./Image.module.scss";

function Image() {
  const { file } = useStore();
  const { data } = useFile(file);
  return <img alt="" className={classes.img} src={data} />;
}

export default Image;
