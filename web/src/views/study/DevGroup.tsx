/** 开发者面板里的一组：一行一个可改名的条目，末尾一个新增框。 */
interface Row {
  key: string;
  value: string;
  onRename: (text: string) => void;
  onRemove: () => void;
}

interface Props {
  title: string;
  rows: Row[];
  draft: string;
  onDraft: (text: string) => void;
  onAdd: () => void;
  addLabel: string;
}

export function Group(props: Props) {
  return (
    <div className="dev__group">
      <p className="dev__title">{props.title}</p>
      <ul className="dev__rows">
        {props.rows.map((row) => (
          <li className="dev__row" key={row.key}>
            <input
              key={row.key + "|" + row.value}
              className="dev__input"
              defaultValue={row.value}
              aria-label={"改名 " + row.value}
              onBlur={(event) => row.onRename(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") event.currentTarget.blur();
                if (event.key === "Escape") event.currentTarget.value = row.value;
              }}
            />
            <button
              type="button"
              className="dev__del"
              aria-label={"删除 " + row.value}
              onClick={row.onRemove}
            >
              ✕
            </button>
          </li>
        ))}
        {props.rows.length ? null : <li className="dev__empty">还没有。</li>}
      </ul>
      <div className="dev__add">
        <input
          className="dev__input"
          value={props.draft}
          aria-label={props.addLabel + "：填名字"}
          placeholder={props.addLabel}
          onChange={(event) => props.onDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") props.onAdd();
          }}
        />
        <button type="button" className="dev__addbtn" onClick={props.onAdd}>
          {props.addLabel}
        </button>
      </div>
    </div>
  );
}
