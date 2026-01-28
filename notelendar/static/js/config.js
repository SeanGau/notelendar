$('form').submit(function (e) {
  e.preventDefault()
  header = $(this).find('input[name="title"]').val();
  header = header.replace(/(\r\n?|\n|\t)/g, "<br>");
  if (header.replace("<br>", "").length < 1) {
    let dialog = confirm("空值會導致此欄位被移除且!!!無法復原!!!，是否確定？");
    if (!dialog) {
      location.reload(true);
      return;
    }
  }

  $.ajax({
    type: "POST",
    url: "/api/update-header",
    data: JSON.stringify({
      'key': $(this).find('input[name="key"]').val(),
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

  location.reload(true);
})