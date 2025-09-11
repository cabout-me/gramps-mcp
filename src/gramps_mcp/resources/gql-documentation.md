# GQL - the Gramps Query Language

GQL is a query language for Gramps genealogy databases. Use it to construct search queries for finding specific records.

## Syntax

A GQL query is a string composed of statements of the form `property operator value`, optionally combined with the keywords `and` and `or` as well as parentheses.

### Properties

#### `class`

Filters for the Gramps object class and can be one of `person`, `family`, `event`, `place`, `citation`, `source`, `repository`, `media`, or `note`.

#### Object properties

GQL supports querying nested properties of Gramps objects, e.g. `primary_name.date.calendar`. See below for a full list of properties – see also [Gramps Data Model](https://gramps-project.org/wiki/index.php/Gramps_Data_Model).

#### List elements by index

Individual elements in list-like properties can be accessed by positional index in square brackets. This can be combined with nested properties, e.g. `primary_name.surname_list[0].surname`.

#### `length`

This is a special property that returns the length of an array-like Gramps property, e.g. `media_list.length > 0` to get objects with media references.

#### `all`, `any`

Two more special properties for array-like Gramps properties. `all` requires a condition to apply to all items of the list, `any` requires it to apply to at least one item. Both properties can be combined with other properties before and after. Examples: `media_list.any.citation_list.length > 0` to return objects with media references that have citations; `media_list.all.citation_list.length = 0` to return objects where all media objects do not have citations.

#### Array index

A numerical array index can be used to access specific elements of a list, e.g. `child_ref_list[0]` for the first child.

#### `get_person`, etc.

While all the preceding properties refer to a single Gramps object, it is also possible to filter on different objects referred to by the initial object. For instance, an event has a place handle in its `place` property. Using the `get_place` pseudo-property, GQL switches to the properties of that object. For instance, it is possible to search for `class = event and place.get_place.name.value ~ York`. This can also be combined with `any` or `all`, e.g. `class = person and event_ref_list.any.ref.get_event.description ~ farmer`.

### Operators

#### `=`, `!=`

Equality or inequality. Examples: `class = person`, `class != family`

#### `>`, `>=`, `<`, `<=`

Comparison. Works for strings as well as numbers. Examples: `confidence <= 1`, `change > 1712477760 `, `gramps_id > "I2015"`

#### `~`, `!~`

Contains or does not contain. Works for lists as well as strings. Examples: `gramps_id !~ F00`, `author ~ David`, `family_list ~ "3a16680f7d226e3ac3eefc8b57a"`

#### No operator/value

If no operator and value is given, the value is interpreted as a boolean (true or false). This works for
all types of properties and Python rules for casting to true/false are applied. For instance, the query `private` returns private objects; `confidence` returns objects where confidence is greater than 0; `media_list` returns objects with at least one media reference.

### Values

Values can be numbers or strings. If numbers should be interpreted as strings or special characters like = are involved, enclose the value in strings. Examples: `gramps_id = F0001`, but `gramps_id = "0001"`.

## Commented examples

```sql
class = note and private and text.string ~ David
```

All private notes that contain the string "David" in their text


```sql
media_list.length >= 10
```

All objects (of any class) with 10 or more media references

```sql
class != person and media_list.any.rect
```

All objects that are *not* a person but have a media reference that is part of an image. Here, `media_list.any.rect` means that for each of the items in the media list, it is checked whether the `rect` (rectangle) property has a truthy value, meaning it is a non-empty list. (`media_list.any.rect.length > 0` would have the same effect.)

```sql
class = family and child_ref_list.length > 10
```

Families with more than 10 children.

```sql
class = event and date.modifier = 0 and date.dateval[2] > 2020
```

Events where the date is a normal date (not a range etc.) and the year is after 2020.

```sql
note_list.any.get_note.text.string ~ "David"
```

All objects with at least one note that contains the string "David" in their text.


```sql
class = family and child_ref_list.all.ref.get_person.gender = 0 and child_ref_list.length = 3
```

All families with three daughters.



## Full list of Gramps Properties

The following properties of Gramps objects exist as of Gramps 5.2.

Here, `[]` indicates array properties, on which index (`[0]` etc.), `any`, `all`, and `length` are supported.

Obviously, many of those properties are only present on some of the primary Gramps object types.

```
abbrev
address_list
address_list[]._class
address_list[].citation_list
address_list[].city
address_list[].country
address_list[].county
address_list[].date
address_list[].date._class
address_list[].date.calendar
address_list[].date.dateval
address_list[].date.modifier
address_list[].date.newyear
address_list[].date.quality
address_list[].date.sortval
address_list[].date.text
address_list[].locality
address_list[].note_list
address_list[].phone
address_list[].postal
address_list[].private
address_list[].state
address_list[].street
alt_loc
alt_loc[]._class
alt_loc[].city
alt_loc[].country
alt_loc[].county
alt_loc[].locality
alt_loc[].parish
alt_loc[].phone
alt_loc[].postal
alt_loc[].state
alt_loc[].street
alt_names
alt_names[]._class
alt_names[].date
alt_names[].date._class
alt_names[].date.calendar
alt_names[].date.dateval
alt_names[].date.modifier
alt_names[].date.newyear
alt_names[].date.quality
alt_names[].date.sortval
alt_names[].date.text
alt_names[].lang
alt_names[].value
alternate_names
alternate_names[]._class
alternate_names[].call
alternate_names[].citation_list
alternate_names[].date
alternate_names[].date._class
alternate_names[].date.calendar
alternate_names[].date.dateval
alternate_names[].date.modifier
alternate_names[].date.newyear
alternate_names[].date.quality
alternate_names[].date.sortval
alternate_names[].date.text
alternate_names[].display_as
alternate_names[].famnick
alternate_names[].first_name
alternate_names[].group_as
alternate_names[].nick
alternate_names[].note_list
alternate_names[].private
alternate_names[].sort_as
alternate_names[].suffix
alternate_names[].surname_list
alternate_names[].surname_list[]._class
alternate_names[].surname_list[].connector
alternate_names[].surname_list[].origintype
alternate_names[].surname_list[].origintype._class
alternate_names[].surname_list[].origintype.string
alternate_names[].surname_list[].prefix
alternate_names[].surname_list[].primary
alternate_names[].surname_list[].surname
alternate_names[].title
alternate_names[].type
alternate_names[].type._class
alternate_names[].type.string
attribute_list
attribute_list[]._class
attribute_list[].citation_list
attribute_list[].note_list
attribute_list[].private
attribute_list[].type
attribute_list[].type._class
attribute_list[].type.string
attribute_list[].value
author
birth_ref_index
change
checksum
child_ref_list
child_ref_list[]._class
child_ref_list[].citation_list
child_ref_list[].frel
child_ref_list[].frel._class
child_ref_list[].frel.string
child_ref_list[].mrel
child_ref_list[].mrel._class
child_ref_list[].mrel.string
child_ref_list[].note_list
child_ref_list[].private
child_ref_list[].ref
citation_list
code
confidence
date
date._class
date.calendar
date.dateval
date.modifier
date.newyear
date.quality
date.sortval
date.text
death_ref_index
desc
description
event_ref_list
event_ref_list[]._class
event_ref_list[].attribute_list
event_ref_list[].attribute_list[]._class
event_ref_list[].attribute_list[].citation_list
event_ref_list[].attribute_list[].note_list
event_ref_list[].attribute_list[].private
event_ref_list[].attribute_list[].type
event_ref_list[].attribute_list[].type._class
event_ref_list[].attribute_list[].type.string
event_ref_list[].attribute_list[].value
event_ref_list[].citation_list
event_ref_list[].note_list
event_ref_list[].private
event_ref_list[].ref
event_ref_list[].role
event_ref_list[].role._class
event_ref_list[].role.string
family_list
father_handle
format
gender
gramps_id
handle
lat
lds_ord_list
lds_ord_list[]._class
lds_ord_list[].citation_list
lds_ord_list[].date
lds_ord_list[].date._class
lds_ord_list[].date.calendar
lds_ord_list[].date.dateval
lds_ord_list[].date.modifier
lds_ord_list[].date.newyear
lds_ord_list[].date.quality
lds_ord_list[].date.sortval
lds_ord_list[].date.text
lds_ord_list[].famc
lds_ord_list[].note_list
lds_ord_list[].place
lds_ord_list[].private
lds_ord_list[].status
lds_ord_list[].temple
lds_ord_list[].type
long
media_list
media_list[]._class
media_list[].attribute_list
media_list[].attribute_list[]._class
media_list[].attribute_list[].citation_list
media_list[].attribute_list[].note_list
media_list[].attribute_list[].private
media_list[].attribute_list[].type
media_list[].attribute_list[].type._class
media_list[].attribute_list[].type.string
media_list[].attribute_list[].value
media_list[].citation_list
media_list[].note_list
media_list[].private
media_list[].rect
media_list[].ref
mime
mother_handle
name
name._class
name.date
name.date._class
name.date.calendar
name.date.dateval
name.date.modifier
name.date.newyear
name.date.quality
name.date.sortval
name.date.text
name.lang
name.value
note_list
page
parent_family_list
path
person_ref_list
person_ref_list[]._class
person_ref_list[].citation_list
person_ref_list[].note_list
person_ref_list[].private
person_ref_list[].ref
person_ref_list[].rel
place
place_type
place_type._class
place_type.string
placeref_list
placeref_list[]._class
placeref_list[].date
placeref_list[].date._class
placeref_list[].date.calendar
placeref_list[].date.dateval
placeref_list[].date.modifier
placeref_list[].date.newyear
placeref_list[].date.quality
placeref_list[].date.sortval
placeref_list[].date.text
placeref_list[].ref
primary_name
primary_name._class
primary_name.call
primary_name.citation_list
primary_name.date
primary_name.date._class
primary_name.date.calendar
primary_name.date.dateval
primary_name.date.modifier
primary_name.date.newyear
primary_name.date.quality
primary_name.date.sortval
primary_name.date.text
primary_name.display_as
primary_name.famnick
primary_name.first_name
primary_name.group_as
primary_name.nick
primary_name.note_list
primary_name.private
primary_name.sort_as
primary_name.suffix
primary_name.surname_list
primary_name.surname_list[]._class
primary_name.surname_list[].connector
primary_name.surname_list[].origintype
primary_name.surname_list[].origintype._class
primary_name.surname_list[].origintype.string
primary_name.surname_list[].prefix
primary_name.surname_list[].primary
primary_name.surname_list[].surname
primary_name.title
primary_name.type
primary_name.type._class
primary_name.type.string
private
pubinfo
reporef_list
reporef_list[]._class
reporef_list[].call_number
reporef_list[].media_type
reporef_list[].media_type._class
reporef_list[].media_type.string
reporef_list[].note_list
reporef_list[].private
reporef_list[].ref
source_handle
tag_list
text
text._class
text.string
text.tags
text.tags[]._class
text.tags[].name
text.tags[].name._class
text.tags[].name.string
text.tags[].ranges
text.tags[].value
title
type
type._class
type.string
urls
urls[]._class
urls[].desc
urls[].path
urls[].private
urls[].type
urls[].type._class
urls[].type.string
```