# littlechat

## Chat example

* Chinese character example
  ![chat example](./imgs/client_page.png)
* emoji example
  ![chat example](./imgs/client_page_emoji.png)

## About

A little chatroom run in console, write in python base
on [`urwid`](https://github.com/urwid/urwid) and `UDP`,
only support Linux, OSX, Cygwin or other unix-like OS, not support Windows

## Quick Start

### Install

#### From repository

* From github

```shell
pip install git+https://github.com/yujun2647/littlechat.git
```

* From gitee

```shell
pip install git+https://gitee.com/walkerjun/littlechat.git
```

#### From Pypi

```shell
pip install littlechat
```

### Usage

#### Start server

* start server at port: 5000

```shell
lchat -t server -sp 5000
```

#### Connect with client

* connect server above

```shell
lchat -sp 5000
```

## Hotkeys supports

| Name            | Use                                       | 
|-----------------|-------------------------------------------|
| `Alt` + `Enter` | force to start a new line at input box    |
| `Alt` + `e`     | open emoji box                            |
| `Alt` + `l`     | keep focus in the edit box (Author needs) |
