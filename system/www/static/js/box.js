(function (exports, ng, $) {
    'use strict';

    /**
     * @var Object box
     */
    var box = ng.module('box', ['ngResource', 'ui.router', 'infinite-scroll', 'ngSanitize']);
    exports.box = box;
	
	/* Repeat directive that activates tooltip  on loaded devices for device info on mouseover*/
	box.directive('deviceRepeatDirective', function ($compile, $timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attr) {
                if (scope.$last === true) {
                    $timeout(function () {
                        scope.$emit('deviceRepeatDirective');
						var template = '<li class="divider"></li><li id="allDevices" class="device active"><a href="javascript:void(0)" ng-click="infinity.nextPage(-1)">All devices</a></li>';
			            var linkFn = $compile(template);
			            var content = linkFn(scope);
			            element.parent().append(content); 

						/*$(".navbar").sticky();*/

			            $('#deviceDropdown li').unbind();
						$('#deviceDropdown li').bind("click", function()
						{
						  $('#deviceDropdown').delay(500).fadeOut(600);
						  scope.$emit('ngRepeatFinished', $( this ).attr("id"));
						});

						scope.$emit('ngRepeatFinished', -1);
                    });
                }
            }
        }
     });

	box.directive('fileModel', ['$parse', function ($parse) {
	    return {
	        restrict: 'A',
	        link: function(scope, element, attrs) {
	            var model = $parse(attrs.fileModel);
	            var modelSetter = model.assign;
	            
	            element.bind('change', function(){
	                scope.$apply(function(){
	                    modelSetter(scope, element[0].files[0]);
	                });
	            });
	        }
	    };
	}]);

	box.service('fileUpload', ['$http', function ($http) {
	    this.uploadFileToUrl = function(file, uploadUrl){
	        var fd = new FormData();
	        fd.append('file', file);
	        $http.post(uploadUrl, fd, {
	            transformRequest: angular.identity,
	            headers: {'Content-Type': undefined}
	        })
	        .success(function(){
	        })
	        .error(function(){
	        });
	    }
	}]);

	/* Repeat directive that manages thumbnail repeats */
	box.directive('thumbnailRepeatDone', function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attr) {
                if (scope.$last === true) {
                    $timeout(function () {
                        eval(attr.thumbnailRepeatDone);
                    });
                }
            }
        }
     });
	
	// Infinity constructor function to encapsulate HTTP and pagination logic
	box.factory('Infinity', function($http) {
	  var Infinity = function($scope) {
	  	this.publish = $scope;
	  	
	  	// Devices
	  	this.publish.imagecount = 0; 
	  	this.publish.videocount = 0; 
	  	this.publish.othercount = 0; 

	  	// Shopping cart
	  	this.publish.product = "9x12cm"; 
		this.publish.price = 2;
		this.publish.shipping = 45;
		this.publish.cart = [];
		this.publish.share = [];
		this.publish.favourite = [];
		this.publish.shared = [];
		this.publish.orderid = false;
		this.publish.config = {};
		this.publish.currentDevice = null;
		this.photolist = new Object();

		// File detail dialog
		this.publish.selectedIndex = -1;

	    // Keep track of Infinite Scroll
	    this.busy = false;
	    this.page = 1;
		this.device = -1; 
		this.type = null; 
		this.lastCount = -1; 

		// Local variables
		this.imageCount = -1; 
		this.device_info = null;
	};

	  // Todo, move this from infinity to device 
	  Infinity.prototype.editDevice = function(device, new_device) {
	  	  if(device == null) {
	  	  	device = this.device; 
	  	  }

		  $('#deviceModal').attr("device", device);	

		  $.ajax({
			    url : "/device/detail?id="+device,
				async: false,
				context: this,
			    success : function(result){
			    	$('#dev_passform').hide();
			    	$("#password-controller").show()
			    	if(new_device) {
			    		$("#deviceModalLabel").text("Set up this new device");
			    		$("#new-desc").show();
			    		$("#dev-delete").hide();
			    	} else {
						$("#deviceModalLabel").text("Edit device information");
			    		$("#new-desc").hide();
			    		$("#dev-delete").show();
			    	}

			        $("#deviceModalInput").attr("value", result.product_name);
			        $("#device-type").val(result.type);
			        $('#deviceModal').modal('show');				
			        this.device_info = result; 
			        $("#device-message").remove();
			        if(this.device != -1) {
			        	var last_backup = new Date(this.device_info.last_backup*1000);
						var last_backup_string = ""; 
						
						if(this.device_info.last_backup > 0) {
							last_backup_string = "Last backup of this device was: "+ (last_backup.getYear()+1900)+"-"+ ('0' + last_backup.getMonth()).slice(-2)+"-"+('0' + last_backup.getDate()).slice(-2);
						}

			        	//$("#infiniteContainer").before("<div id='device-message' style='background-color: #DDD; padding: 5px; padding-left: 15px; margin-bottom: 10px;  '><div style='float: left;'><b>"+this.device_info.product_name+"</b> (<a href='#' onClick=\"$('#deviceDetailModal').modal('show')\">Change name</a>) – "+this.device_info.image_count+" images and "+this.device_info.video_count+" videos. "+last_backup_string+"</div><div style='float: right;'></div><br style='clear:both;' /></div>");
			        }
			    },
			    error: function (xhr, ajaxOptions, thrownError) {
			        alert(xhr.status);
			        alert(thrownError);
				}	
		  });	  	
	  }

	  // Todo, move this from infinity to device 
	  Infinity.prototype.updateDevice = function() {
	  	if($("#dev_password").val() != "" && $("#dev_password").val() != $("#dev_confirmPassword").val()) {
	  		alert("Sorry, passwords are not matching. Please check your spelling.");
	  		return false;
	  	} else {
			$.ajax({
			    url : "/device/update?id="+$('#deviceModal').attr("device")+"&product_name="+$("#deviceModalInput").val()+"&type="+$("#device-type").val()+"&password="+$("#dev_password").val(),
				async: false,
				context: this,
			    success : function(result){
			        window.location = "/"; 
			    },
			    error: function (xhr, ajaxOptions, thrownError) {
			        alert(xhr.status);
			        alert(thrownError);
				}
			}); 	  		
	  	}
	  }

	  // Todo, move this from infinity to device 
	  Infinity.prototype.login = function() {
	  	if(confirm("This will completely remove this device, are you sure you want to do this?")) {
			$.ajax({
			    url : "/device/erase?id="+$('#deviceModal').attr("device"),
				async: false,
				context: this,
			    success : function(result){
			        window.location = "/"; 
			    },
			    error: function (xhr, ajaxOptions, thrownError) {
			        alert(xhr.status);
			        alert(thrownError);
				}	  	
			});
		} else {
			return false;
		}
	  }

	  // Todo, move this from infinity to device 
	  Infinity.prototype.eraseDevice = function() {
	  	if(confirm("This will completely remove this device, are you sure you want to do this?")) {
			$.ajax({
			    url : "/device/erase?id="+$('#deviceModal').attr("device"),
				async: false,
				context: this,
			    success : function(result){
			        window.location = "/"; 
			    },
			    error: function (xhr, ajaxOptions, thrownError) {
			        alert(xhr.status);
			        alert(thrownError);
				}	  	
			});
		} else {
			return false;
		}
	  }

	  Infinity.prototype.init = function(username) {
	  	this.publish.username = username; 
	  }

	  Infinity.prototype.selectTab = function(state){
		if(this.publish.state != state) {
			this.publish.state = state;
		} else {
			this.publish.state = null;
		}

		$('#order-form').bootstrapValidator();		
	  }

	  Infinity.prototype.editProfile = function(state){
	  	$('#profile-picture').attr('src', '/files/stream/null/null/profile/0?'+(new Date()).getTime());
	  	$('#userModal').modal('show');
	  }

	  Infinity.prototype.cancelSharing = function(state){
	  	this.publish.share = [];
	  }

	  Infinity.prototype.deleteFile = function(state){
	  		var file_id = $("#filesDetailModalLabel").attr("file");
			
			$.get( "/files/hide?id="+file_id, function( data ) {
			  if(data == "ok") {
				  $("#photo-"+file_id).parent().hide();
			  }
			});
			
			$('#filesDetailModal').modal('hide');
	  }

	  Infinity.prototype.shareImages = function(state){
		$.isLoading({ text: "Publishing files... " });

		var images = []; 
		var scp = this; 
		var descriptions = ""; 

		$.each( this.publish.share, function( key, value ) {
		  images.push(value.id);
		  descriptions += "&description-"+value.id+"="+encodeURIComponent($("#description-"+value.id).val()); 
		});

		$http({ method: 'GET', url: "/upload?files="+images.join(",")+descriptions }).
			success(function(data, status, headers, config) {

		    	if(data == "error") {
		    		alert("Your order could not be placed at this moment.");
		    	} else {
		            $.isLoading( "hide" );
		    		scp.publish.share = [];
		    		scp.loadShared();
		            $(".busy").show();
		            pendingPublish();
					intervalID = setInterval(pendingPublish, 5000);

		    	}

			}).
			error(function(data, status, headers, config) {
				alert("Your images could not be shared at this moment. " + data);
			});
	  }

	  Infinity.prototype.placeOrder = function(event){
		$("#order-form").data('bootstrapValidator').validate();

		if(!$("#order-form").data('bootstrapValidator').isValid()) {
			return;
		}

		var images = []; 
		var scp = this; 
		$.each( this.publish.cart, function( key, value ) {
		  images.push(value.id);
		});

		//$(event.target).isLoading({ text: "Placing order", position: "overlay" });

		$.isLoading({ text: "Submitting order... " });	        

		$http({ method: 'GET', url: "/print?files="+images.join(",")+"&recipient_name="+$("#recipient_name").val()+"&address_1="+$("#address_1").val()+"&address_town_or_city="+$("#address_town_or_city").val()+"&postal_or_zip_code="+$("#postal_or_zip_code").val()+"&country="+$("#country").val() }).
			success(function(data, status, headers, config) {

		    	if(data == "error") {
		    		alert("Your order could not be placed at this moment.");
		    	} else {
		            $.isLoading( "hide" );
		    		scp.publish.orderid = data;
		    		scp.publish.cart = [];
		    		scp.$apply();
		    	}

			}).
			error(function(data, status, headers, config) {
				alert("Your order could not be placed at this moment. " + data);
			});
	  }

	  // Used in cart for switching between printing options
	  Infinity.prototype.selectProduct = function(event){
	  	var price = $(event.target).find("strong").text();
		this.price = price.replace("kr", "");

	  	var product = $(event.target).find("span").text();	  
	  	var shipping = $(event.target).parent().attr("shipping");
	  	
		this.publish.shipping = parseInt(shipping);
		this.publish.product = product;
		this.publish.price = parseInt(this.price);
		
		$(".pricelist ul li").removeClass('active');
		$(event.target).addClass('active');
	  }

	  // Adds a photo to the pringin queue
	  Infinity.prototype.addToCart = function(image, event){		
		var currentImageId = this.publish.currentFile.id; 
		if(!$.grep(this.publish.cart, function(e){ return e.id == currentImageId; }).length == 1) {
			$("#photo-"+this.publish.currentFile.id+" .print").addClass("visible");
			this.publish.cart.push(this.publish.currentFile);
		} else {
			//this.publish.cart.splice(cartIndex, 1);
			this.publish.cart = $.grep(this.publish.cart, function(e){ return e.id == currentImageId; }, true)
			$("#photo-"+this.publish.currentFile.id+" .print").removeClass("visible");	
		}
		
		// If added from file modal, close it
		$('#filesDetailModal').modal('hide');
	  }

	  // Adds a photo to the pringin queue
	  Infinity.prototype.favourite = function(image, event){		
		if(!$.grep(this.publish.favourite, function(e){ return e.id == image.id; }).length == 1) {
			$(event.target).removeAttr('style');
			$(event.target).addClass('active');
			this.publish.favourite.push(image);
		} else {
			this.publish.favourite = $.grep(this.publish.favourite, function(e){ return e.id == image.id; }, true)
			$(event.target).removeClass('active');
			$(event.target).css('background-image', 'url(/static/images/star-off.png)');
		}		
	  }

	  // Adds a photo to the pringin queue
	  Infinity.prototype.share = function(image, event){		
		var currentImageId = this.publish.currentFile.id; 
		this.publish.share.push(this.publish.currentFile);
		// If added from file modal, close it
		$('#filesDetailModal').modal('hide');
	  }

	  Infinity.prototype.previousPicture = function( ) {
	  	if(this.publish.selectedIndex > 0) {
	  		this.showPicture(this.publish.items[this.publish.selectedIndex-1].id);
	  	}
	  }

	  Infinity.prototype.nextPicture = function( ) {
	  	if(this.publish.selectedIndex < this.publish.items.length - 1) {
	  		this.showPicture(this.publish.items[this.publish.selectedIndex+1].id);
	  	}
	  }

	  // Todo, move this from infinity to device 	  
	  Infinity.prototype.showPicture = function(file, indexvalue) {
	  	var obj = this.publish.items.filter(function( obj, index ) {
		  return obj.id == file;
		})[0];
		
		if (obj == null) {
			obj = this.publish.shared.filter(function( obj ) {
			  return obj.id == file;
			})[0];
		}

		if(this.publish.items.indexOf(obj) >= 0) {
			this.publish.selectedIndex = this.publish.items.indexOf(obj);
		}

		if(this.publish.selectedIndex == 0) {
			$(".nav-left").hide();
		} else {
			$(".nav-left").show();
		}

		if(this.publish.selectedIndex == this.publish.items.length -1) {
			$(".nav-right").hide();
		} else {
			$(".nav-right").show();
		}


	  	//var obj = JSON.parse(file);
	  	
	  	if(obj.locked == 1) {
	  		$("#loginModal").modal("show");
	  		return false;
	  	}

		if(this.publish.config["ISLOCAL"] == true) {
			$(".islocal").show();
		}

	  	this.publish.currentFile = obj; 

		var ts = new Date(null);
		ts.setTime(obj.created_at*1000);
		
		var time = new Date(obj.created_at*1000);
		var viewMonth = time.getMonth();
		var viewYear = time.getFullYear().toString();
		var viewDate = time.getDate();
		var month = Array("January","February","March","April","May","June","July","August","September","October","November","December");
		
		if(obj.product_name)
			$("#filesDetailModalLabel").html(obj.product_name + " > " + obj.name);
		else 
			$("#filesDetailModalLabel").html(obj.name);

		$("#filesDetailModalDate").html(viewDate +" "+ month[viewMonth] + ", "+viewYear);
		$("#filesDetailModalLabel").attr("file", obj.id);
		
		if(obj.type == "video") {
			$("#moddalVideoContainer").html('<video id="modalVideo" style="display: none;" width="100%" height="520" controls="controls" autoplay="autoplay"><source id="modalSource" src="" type="video/mp4" /></video>');					
			$("#modalVideo > source").attr("src", "/files/stream/"+obj.id+"/null/nodownload/0");
			$("#originalImage").attr("src", "/files/stream/"+obj.id+"/null/full/0");
			$("#modalVideo").load();
			$("#modalVideo").show();
			$("#modalImage").hide();
			$("#print-button").hide();
		} else {
			$("#originalImage").attr("src", "/files/stream/"+obj.id+"/null/full/0");
			$("#modalVideo").hide();
			$("#modalImage").show();
			$("#zoomLink").attr("href", "/files/stream/"+obj.id+"/null/nodownload/0");
			$("#modalImage").attr("src", "/files/stream/"+obj.id+"/null/thumbnail/520");
			$("#print-button").show()
		}
		
		if($.grep(this.publish.cart, function(e){ return e.id == obj.id; }).length == 1) {
			$("#print-label").html("Remove from cart");
		} else {
			$("#print-label").html("Add to cart");
		}

        $('#filesDetailModal').modal('show');
	  }

	  Infinity.prototype.loadShared = function() {
			$.ajax({
			    url : "/files?mode=shared",
				async: false,
				context: this,
			    success : function(result) {
					this.publish.shared = [];
					// Loop JSON response and add images to ng-repeat array
				    for(var i = 0; i < result.files.length; i++) {
					      this.publish.shared.push({description:result.files[i].description, name:result.files[i].name, background:result.files[i].thumbnail, id:result.files[i].file, created_at:result.files[i].created_at, type:result.files[i].type, type_content:""});
				    }
			    }
			});
	  };
	  
	  /**
	  * Method that loads next page in the infinite scroll. Device ID and File type ID can be passed as filtering parameters. 
	  *	  
	  **/
	  Infinity.prototype.nextPage = function(_device, _type, noInvert, tab) {
	    // Make sure previous request is not running
	    if (this.busy) return;

	    // Flag this method as running
	    this.busy = true;	
	   	var filters = [];

	    if(_type == "other") {
		    if(!noInvert) {
		    	$("#filter-"+_type).prop("checked", !$("#filter-"+_type).prop("checked"));
		    }

			$("#filter-image").prop("checked", !$("#filter-other").prop("checked"));
			$("#filter-video").prop("checked", !$("#filter-other").prop("checked"));
			
			if(!$("#filter-"+_type).prop("checked")) {
				_type = "image,video";
				this.type = _type;
			}
	    } else 
	    if(_type != null) {
			this.type = _type;	    	
		    
		    if(!noInvert) {
		    	$("#filter-"+_type).prop("checked", !$("#filter-"+_type).prop("checked"));
		    }
	    	
	    	if($('#filter-other').prop('checked')) {
	    		$('#filter-other').prop('checked', false);
	    	}
	    } 	

	   	// Get selected filters
		$( "li.filters input" ).each(function( index ) {
		  if($( this ).prop("checked")) {
		  	filters.push($( this ).prop("id").replace("filter-", ""));
		  }
		});	   


	    // Parameter to determine wether content was replaced or appended. replace => chnageState = true
	    var changedState = false; 

		// If a device ID was passed, let's filter on device
		if((_device) || _type) {
			changedState = true;
			this.lastCount = -1; 

			// If a new device was selected, show selected device in dropdown
			if(_device && _device != -1 && this.device != _device) {
				this.device = _device;
				$("#device-dropdown").text($("#"+_device + " span").text());
				$(".device").removeClass("active");
				$("#"+_device).addClass("active");
				$("#deviceCount").hide();

				// Set current device
				for(var i=0; i<this.publish.service.devices.length; i++) {
					if(this.publish.service.devices[i].id == _device) {
						this.publish.currentDevice = this.publish.service.devices[i];
					}
				}
			} else 
			// Restore everything back to normal. Showing all devices
			if(_device) {
				this.device = -1; 
				$(".device").removeClass("active");
				$("#allDevices").addClass("active");
				$("#device-dropdown").text('All devices');
				$("#deviceCount").show();
				changedState = true; 
				this.publish.currentDevice = null;
				//$(".dropdown-menu").hide();
			}
		}
		
		// Clear visiable area of old images if the state was changed
		if(changedState == true) {
			this.page = 1; 			
			this.publish.items = [];
			this.publish.files = [];
			resetDate();
		}
		
		// Format input string to request page
		if(this.device == null) {
			this.device = -1;
		}

		// Lead request
		if(changedState || this.type != "other" && this.lastCount != 0) {
			$.ajax({
			    url : "/files?after="+this.page+"&device="+this.device+"&format="+filters.join(","),
				async: false,
				context: this,
			    success : function(result){
			    	if(changedState == true) {
						if (!window.matchMedia || (window.matchMedia("(max-width: 767px)").matches)) {
							$("#mainNav").css("height", "0px");
							$("#mainNav").removeClass("in");
							$("#mainNav-btn").addClass("collapsed");
						}
					}

					// If response resulted in no images, show error message
					if(result.files.length == 0 && this.publish.items.length == 0) {
						this.publish.missingImages = true;
					} else {
						this.publish.missingImages = false; 
					}
					
					this.lastCount = result.files.length; 

					// Loop JSON response and add images to ng-repeat array
				    for(var i = 0; i < result.files.length; i++) {
				      var type_content = ""; 
				      
				      // If current item is a video, add info about lenght in thumbnail. 
				      /*if(result.files[i].type == "video" && result.files[i].value != null) {
				      	  var video_length = result.files[i].value.split(" ")
				      	  var suffix = "ms"; 
				      	  
				      	  for (var ind = 0; ind < video_length.length; ++ind) {
				      	  	if(video_length[ind].indexOf(suffix, video_length[ind].length - suffix.length) == -1)
								type_content += video_length[ind].replace("mn", "min")+" ";
						  }
				      }	*/	
				      
				      // Push thumbnail item to ng-repeat array	  
				      if(filters == "other") {
					      var _months = Array("January","February","March","April","May","June","July","August","September","October","November","December");
					      var time = new Date(result.files[i].created_at*1000);
						  var viewMonth = String(_months[time.getMonth()]).substr(0, 3);
						  var viewYear = time.getFullYear().toString();
						  var viewDate = time.getDate();
						  var dat = viewYear + "-" + viewMonth + "-" + viewDate;
						  
					      this.publish.files.push(['<img src="/icon/'+result.files[i].type+"-"+result.files[i].subtype+'" />', '<a href="/files/stream/'+result.files[i]._id+'/'+result.files[i].name+'/full/0">'+result.files[i].name+'</a>', dat, humanFileSize(result.files[i].size)]);				      
				      } else {
				      	  _type = result.files[i].type; 
					      this.publish.items.push({description:result.files[i].description, product_name:result.files[i].product_name, name:result.files[i].name, background:result.files[i].thumbnail, id:result.files[i].file, created_at:result.files[i].created_at, type:_type, type_content:type_content});				      
				      }
				    }			    

					// Increase current page number(for next request)
			        this.page = this.page + 1;
			        this.busy = false;

					if(filters == "other" && this.publish.files.length > 0) {
						this.publish.datatable.fnClearTable();
						this.publish.datatable.fnAddData(this.publish.files);
					}

					if(_type != null) {
						this.type = _type;
					}
				
			    }
			});
		} else {
			this.busy = false; 
		}
	  };
	  return Infinity;
	});	

    /**
     * Configure the box app
     */
    box.config(function ($stateProvider, $urlRouterProvider) {

        $urlRouterProvider.otherwise('/');
		
		// When the application starts we are lading device list and first page of the result. 
        $stateProvider
            .state('files', {
                url: '/',
                controller: 'FilesCtrl',
                templateUrl: '/templates/files.html'
            })
    });

    /**
     * Run the box app
     */
    box.run(function ($window) {
    });

    /**
     * File service
     */
    box.factory('FileService', function ($resource, $window, $q) {

        /**
         *
         */
        var FileService = function () {
            this.detailsResource = $resource('/files/details');
            this.deviceResource = $resource('/devices');
            this.devices = [];
            this.init = false;
            this.details = [];
        };

        FileService.prototype = {

            /**
             * Successful files load callback
             */
            loadSharedFilesSuccess: function (resource) {
                this.shared = resource.files;
            },

            /**
             * Successful devices load callback
             */
            loadDevicesSuccess: function (data) {
                this.devices = data.devices;
                this.init = true;

				$(".navbar").show();
				$("#deviceCount").html("("+this.devices.length+")");
				$(".device-dropdown").click(function() {
					$(".dropdown-menu").toggle();
				});				
            },


            /**
             * Successful file detail load callback
             */
            loadDetailsSuccess: function (data) {
                if (data['_id'] !== undefined) {
                    this.details[data['_id']] = data;
                }
            },

            /**
             * Failed load callback
             */
            loadError: function (data) {
                //console.log(data);
            },


            /**
             * Load available devices
             */
            loadDevices: function () {
                this.deviceResource.get(
                    {},
                    this.loadDevicesSuccess.bind(this),
                    this.loadError.bind(this)
                );
                return this;
            },
            
            /**
             * Load file by id
             */
            loadDetails: function (id) {
                var that = this,
                    deferred = $q.defer(),
                    resource;

                if (this.details[id] !== undefined) {
                    deferred.resolve();
                } else {
                    resource = this.detailsResource.get(
                        {id: id},
                        function (data) {
                            that.loadDetailsSuccess(data);
                            deferred.resolve();
                        },
                        function (data) {
                            that.loadError(data);
                            deferred.resolve();
                        }
                    );
                }

                return deferred.promise;
            },

            /**
             * Get laoded details
             */
            getDetails: function (id) {
                return this.details[id] || false;
            }
        };

        return new FileService();
    });

    /**
     * Files controller
     */
    box.controller('FilesCtrl', function ($scope, $http, $location, FileService, Infinity, fileUpload) {
        this.fileService = FileService.loadDevices();
        $scope.service = this.fileService;
        $scope.infinity = new Infinity($scope);
        $scope.items = [];
        $scope.files = [];
        $scope.types = {}
        $scope.state = "list"; 
		$scope.infinity.loadShared();

		$http({ method: 'GET', url: "/config" }).
			success(function(data, status, headers, config) {
		    	$scope.infinity.publish.config = data;
		    	if(data["ISLOCAL"] == true) {
		    		$(".islocal").show();
		    	}
		    	$("#firstname").val(data["FIRSTNAME"]);
		    	$("#lastname").val(data["LASTNAME"]);
			});

        if(!$scope.datatable)
	        $scope.datatable = $('#otherfiles').dataTable({ "iDisplayLength": 30, "bLengthChange": false,   "columns": [
			    { "width": "35px" },
			    null,
			    null,
			    null
			  ] });

	    /* Method to save user profile */ 
	    $scope.saveProfile = function(){
	        if($("#password").val() != "" && $("#password").val() != $("#confirmPassword").val()) {
	        	alert("Passwords do not match");
	        	return;
	        }

	        var _pass = "";

	        if($("#password").val()) {
	        	_pass = "&PASSWORD="+$("#password").val(); 
	        }

	        var file = $scope.myFile;
	        var uploadUrl = "/profileupload";
	        fileUpload.uploadFileToUrl(file, uploadUrl);
			
			$http({ method: 'GET', url: "/config/save?FIRSTNAME="+$("#firstname").val()+"&LASTNAME="+$("#lastname").val()+_pass }).
				success(function(data, status, headers, config) {
					$("#fileupload").wrap('<form>').closest('form').get(0).reset();
		  			$("#fileupload").unwrap();
					$("#userModal").modal("hide");					
				}).
				error(function(data, status, headers, config) {
					alert("There was a problem saving your profile information");
				});
	    };


        /* This method runs everytime devices has been loaded. To force UI update.  */
		$scope.$on('ngRepeatFinished', function(ngRepeatFinishedEvent, device) {
			$scope.types = { 'videos' : 0, 'images' : 0, 'others' : 0 };

			if(device > 0) {
				$.each($scope.service.devices, function( index, value ) {
				  if(value.id == device) {
					  for(var key in $scope.types) {
					  	$scope.types[key] = value[key];
					  	$scope.$apply();
					  }
				  }
				});
			} else {
				$.each($scope.service.devices, function( index, value ) {
				  //alert(value.new);						
				  if(value.new == 1) {
				  	$scope.infinity.editDevice(value.id, 1);
				  }

				  for(var key in $scope.types) {
				  	$scope.types[key] += value[key];
					$scope.$apply();
				  }
				});
			}
		});        

        $scope.FilesCtrl = this;
        return this;
    });

}(window, angular, jQuery || {log: function () { 'use strict'; return; }}));
