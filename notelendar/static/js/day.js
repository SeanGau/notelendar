let previousContent = "";
let colWidth = [];

let updateColWidth = function () {
  baseWidth = $("th.date")[0].clientWidth;
  $(".col-title").each(function (index, element) {
    if ($(element).attr("style") && $(element).width() / baseWidth > 1.1) {

      colWidth[index] = $(element).width() / baseWidth;
    } else {
      colWidth[index] = null;
    }
  });
  localStorage.setItem("col_width", colWidth);
}

$(".textarea.note-content, .textarea.note-key").on("focus", function (e) {
  previousContent = $(this).html();
  baseWidth = $("th.date")[0].clientWidth;
  thisOffset = $(this).offset().left;
  if (thisOffset < baseWidth) {
    $("#table-block").scrollLeft($("#table-block").scrollLeft() - baseWidth + thisOffset);
  }
  updateColWidth();
}).on("click", function (e) {
  anchor = document.getSelection();
  lastAnchor = [anchor.focusNode, anchor.focusOffset];
})

let lastAnchor = [];
let isComposing = false;
$(".textarea").on("compositionstart", function (e) {
  isComposing = true;
}).on("compositionend", function (e) {
  isComposing = false;
}).on("keyup", function (e) {
  noteKey = $(this).data('note-key');
  anchor = document.getSelection();
  console.log(anchor.toString().length, e.keyCode, lastAnchor);
  if (isComposing || anchor.toString().length > 0 || (e.keyCode != 37 && e.keyCode != 38 && e.keyCode != 39 && e.keyCode != 40)) {
    lastAnchor = [];
    return;
  }
  switch (e.keyCode) {
    case 37:
      if (anchor.focusNode.isEqualNode(lastAnchor[0]) && anchor.focusOffset == lastAnchor[1]) {
        $(".textarea", $(this).parents("td").prev("td")).focus();
        lastAnchor = [];
      }
      break;
    case 38:
      if (anchor.focusNode.isEqualNode(lastAnchor[0]) && anchor.focusOffset == lastAnchor[1]) {
        $(`.textarea[data-note-key=${noteKey}]`, $(this).parents("tr").prev("tr")).focus();
        lastAnchor = [];
      }
      break;
    case 39:
      if (anchor.focusNode.isEqualNode(lastAnchor[0]) && anchor.focusOffset == lastAnchor[1]) {
        $(".textarea", $(this).parents("td").next("td")).focus();
        anchor.modify('move', 'right', 'documentboundary');
        anchor.collapseToEnd();
        lastAnchor = [];
      }
      break;
    case 40:
      if (anchor.focusNode.isEqualNode(lastAnchor[0]) && anchor.focusOffset == lastAnchor[1]) {
        $(`.textarea[data-note-key=${noteKey}]`, $(this).parents("tr").next("tr")).focus();
        anchor.modify('move', 'right', 'documentboundary');
        anchor.collapseToEnd();
        lastAnchor = [];
      }
      break;
  }
  lastAnchor = [anchor.focusNode, anchor.focusOffset];
})

$(".textarea.note-content").on("blur", function (e) {
  this
  noteDate = $(this).data('note-date');
  noteKey = $(this).data('note-key');
  note = $(this).html();
  if (note == previousContent) {
    return;
  }
  $.ajax({
    type: "POST",
    url: "/api/update-content",
    data: JSON.stringify({
      'noteDate': noteDate,
      'noteKey': noteKey,
      'note': note
    }),
    success: function () {
      console.log("success");
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      alert(XMLHttpRequest.status, XMLHttpRequest.readyState, textStatus);
    },
    contentType: "application/json"
  });
})

$(".textarea.note-key").on("blur", function (e) {
  header = $(this).html();
  header = header.replace(/(\r\n?|\n|\t)/g, "<br>");
  if (header == previousContent) {
    return;
  }
  if (header.replace("<br>", "").length < 1) {
    let dialog = confirm("空值會導致此欄位被移除且!!!無法復原!!!，是否確定？");
    if (!dialog) {
      location.reload(true);
      return;
    } else {
      $(`table [data-note-key=${$(this).data('note-key')}]`).each(function () {
        $(this).parent("th, td").remove();
      })
    }
  }

  $.ajax({
    type: "POST",
    url: "/api/update-header",
    data: JSON.stringify({
      'key': $(this).data('note-key'),
      'value': header
    }),
    success: function () {
      console.log("success");
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      alert(XMLHttpRequest.status, XMLHttpRequest.readyState, textStatus);
    },
    contentType: "application/json"
  })
})

$("td").on("resize", function (e) {
  console.log(this);
})

$("#add-col").on("click", function (e) {
  e.preventDefault();
  $.ajax({
    type: "POST",
    url: "/api/update-header",
    data: JSON.stringify({
      'value': $(".textarea.note-key").length
    }),
    success: function () {
      console.log("success");
      location.reload(true);
    },
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      alert(XMLHttpRequest.status, XMLHttpRequest.readyState, textStatus);
    },
    contentType: "application/json"
  });
})

const url = new URL(window.location.href);

$("#prev-dates").on("click", function (e) {
  e.preventDefault();
  let nowPage = url.searchParams.get("page") || 0;
  url.searchParams.set("page", Number(nowPage) - 1);
  window.location.href = url.href;
})

$("#next-dates").on("click", function (e) {
  e.preventDefault();
  let nowPage = url.searchParams.get("page") || 0;
  url.searchParams.set("page", Number(nowPage) + 1);
  window.location.href = url.href;
})

$("#search").on("click", function (e) {
  e.preventDefault();
  searchString = $("input[name=search]").val();
  sdate = $("input[name=sdate]").val();
  window.location.href = `/?search=${searchString}&sdate=${sdate}`;
})

$("select[name=freeze]").on("change", function (e) {
  e.preventDefault();
  //let freezeCol = url.searchParams.get("freeze") || 0;
  let freezeCol = $(this).val();
  $(".sticky").css({ "left": "" });
  $(".sticky").removeClass("sticky");
  $("tr").each(function () {
    for (let i = 1; i <= freezeCol; i++) {
      let colDom = $($("td,th", this)[i]);
      colDom.css({ "left": $("#table-block").scrollLeft() + colDom.offset().left });
      colDom.addClass("sticky");
    }
  });
  localStorage.setItem("freeze_col", freezeCol);
})

$(function (e) {
  if ($("th.date.today").length > 0) {
    $("#table-block").scrollTop($("th.date.today").offset().top - 2 * 32 - 2 * 48);
  }
  $("select[name=freeze]").val(localStorage.getItem("freeze_col") || 0);
  $("select[name=freeze]").trigger("change");

  baseWidth = $("th.date")[0].clientWidth;
  colWidth = (localStorage.getItem("col_width") || "").split(",");
  console.log(colWidth);
  colWidth.forEach((width, index) => {
    if ($(".col-title")[index]) {
      $($(".col-title")[index]).css({ "width": width * baseWidth });
    }
  });
})